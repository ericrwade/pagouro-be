"""Real-ESRGAN x2 upscale, self-contained. The RRDBNet architecture is re-implemented here in plain
PyTorch (no basicsr/realesrgan packages, whose pinned torchvision import breaks on current torch); the
weights are the official RealESRGAN_x2plus.pth (BSD-3-Clause, xinntao/Real-ESRGAN v0.2.1 release) and are
loaded with strict key matching, so a mismatch fails loudly instead of upscaling with garbage.

    python upscale2x.py <in_dir> <out_dir> [list_file]   # list_file: one filename per line, default: all PNGs
"""
import os, sys, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
import numpy as np

URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"


class RDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1); self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1); self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1); self.lrelu = nn.LeakyReLU(0.2, True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x)); x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1))); x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RRDB(nn.Module):
    def __init__(self, nf, gc=32):
        super().__init__()
        self.rdb1 = RDB(nf, gc); self.rdb2 = RDB(nf, gc); self.rdb3 = RDB(nf, gc)

    def forward(self, x):
        return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x


class RRDBNet(nn.Module):
    def __init__(self, in_ch=3, out_ch=3, nf=64, nb=23, gc=32, scale=2):
        super().__init__()
        self.scale = scale
        self.conv_first = nn.Conv2d(in_ch * 4 if scale == 2 else in_ch, nf, 3, 1, 1)
        self.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
        self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1); self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1); self.conv_last = nn.Conv2d(nf, out_ch, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, True)

    def forward(self, x):
        feat = F.pixel_unshuffle(x, 2) if self.scale == 2 else x
        feat = self.conv_first(feat)
        feat = feat + self.conv_body(self.body(feat))
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))


def main():
    in_dir, out_dir = sys.argv[1], sys.argv[2]
    names = [l.strip() for l in open(sys.argv[3]) if l.strip()] if len(sys.argv) > 3 else sorted(f for f in os.listdir(in_dir) if f.endswith(".png"))
    w = "/workspace/sc/RealESRGAN_x2plus.pth"
    if not os.path.exists(w):
        torch.hub.download_url_to_file(URL, w)
    sd = torch.load(w, map_location="cpu")
    sd = sd.get("params_ema", sd.get("params", sd))
    net = RRDBNet()
    net.load_state_dict(sd, strict=True)   # a key mismatch raises here -> caller skips the upscale
    net = net.eval().cuda().half()
    os.makedirs(out_dir, exist_ok=True)
    with torch.no_grad():
        for n in names:
            im = np.asarray(Image.open(os.path.join(in_dir, n)).convert("RGB")).astype(np.float32) / 255.0
            x = torch.from_numpy(im).permute(2, 0, 1).unsqueeze(0).cuda().half()
            y = net(x).float().clamp_(0, 1)[0].permute(1, 2, 0).cpu().numpy()
            Image.fromarray((y * 255.0).round().astype(np.uint8)).save(os.path.join(out_dir, n))
    print("UPSCALE_DONE", len(names), flush=True)


if __name__ == "__main__":
    main()
