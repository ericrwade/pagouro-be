"""Pagouro BE — the 180 captions for the six-month X showcase (showcase/x180/).

Each row: (category, slug, caption). The caption is appended to the trained prompt prefix
"belleposter, Belle Epoque lithograph poster, " at draw time. No caption asks for words, titles or
signs (the model garbles lettering), none names a living person or a trademark.

    python scripts/showcase_x180_prompts.py  -> writes showcase/x180/captions.jsonl (numbered, round-robin by category)
"""
from __future__ import annotations
import io, json, os, sys
from collections import defaultdict

ROWS = [
    # ---- people (18) ----
    ("people", "woman-parasol-garden", "a young woman in a long white dress with a parasol, standing in a rose garden"),
    ("people", "man-top-hat-cane", "a gentleman in a top hat and frock coat leaning on a cane, in profile"),
    ("people", "woman-large-hat-portrait", "portrait of a woman in an enormous feathered hat, looking over her shoulder"),
    ("people", "couple-boulevard-evening", "an elegant couple strolling arm in arm along a lamplit boulevard at dusk"),
    ("people", "girl-red-ribbon", "a little girl with a red ribbon in her hair holding a kitten"),
    ("people", "man-moustache-bowler", "a man with a curled moustache and a bowler hat, smiling, in profile"),
    ("people", "family-picnic-portrait", "a family of five in summer clothes posing on a lawn under a tree"),
    ("people", "woman-reading-window", "a woman in a blue gown reading a book by a tall window"),
    ("people", "three-friends-cafe", "three young women in striped dresses laughing together at a café table"),
    ("people", "old-fisherman-pipe", "an old fisherman with a white beard smoking a pipe, a harbour behind him"),
    ("people", "woman-fan-opera", "a woman in an evening gown with a folding fan, seated in an opera box"),
    ("people", "boy-sailor-suit", "a boy in a sailor suit holding a wooden toy boat"),
    ("people", "man-bicycle-cap", "a young man in a flat cap and knickerbockers standing beside his bicycle"),
    ("people", "woman-violin", "a woman in a green dress playing the violin"),
    ("people", "soldier-dress-uniform", "a young soldier in a blue dress uniform with a red kepi, standing at ease"),
    ("people", "woman-dog-promenade", "a woman in a tailored walking suit with a small white dog on a leash"),
    ("people", "painter-easel-outdoors", "a painter with a beret at an easel in a sunny meadow"),
    ("people", "group-portrait-balcony", "a group of men and women in evening dress on a balcony overlooking city lights"),
    # ---- landscapes (14) ----
    ("landscapes", "poplars-river-sunset", "a row of tall poplar trees along a river at sunset"),
    ("landscapes", "lavender-fields-provence", "rolling fields of lavender under a hot blue sky"),
    ("landscapes", "mountain-lake-reflection", "a still mountain lake reflecting snowy peaks"),
    ("landscapes", "wheat-field-haystacks", "golden wheat fields with haystacks under a cloudy sky"),
    ("landscapes", "chalk-cliffs-sea", "white chalk cliffs above a calm green sea"),
    ("landscapes", "pine-forest-mist", "a pine forest in morning mist with sunbeams between the trunks"),
    ("landscapes", "river-valley-castle", "a river valley with a castle on a hill and a bridge below"),
    ("landscapes", "olive-grove-hillside", "an olive grove on a terraced hillside with a stone farmhouse"),
    ("landscapes", "waterfall-gorge", "a waterfall tumbling into a rocky gorge"),
    ("landscapes", "sunflower-field-village", "a field of sunflowers in front of a village with a church steeple"),
    ("landscapes", "autumn-forest-path", "a path through an autumn forest in orange and gold"),
    ("landscapes", "moonlit-lake-boat", "a moonlit lake with a lone rowing boat"),
    ("landscapes", "windmill-tulip-field", "a windmill beside a field of red tulips"),
    ("landscapes", "stormy-sea-rocks", "waves crashing on dark rocks under a stormy sky"),
    # ---- everyday activities (14) ----
    ("everyday", "woman-watering-flowers", "a woman watering potted geraniums on a balcony"),
    ("everyday", "man-reading-cafe-terrace", "a man reading a newspaper on a café terrace with a cup of coffee"),
    ("everyday", "laundry-courtyard", "women hanging white laundry in a sunny courtyard"),
    ("everyday", "baker-loaves", "a baker in a white apron carrying a tray of fresh bread loaves"),
    ("everyday", "children-hoop-street", "children rolling a hoop down a cobbled street"),
    ("everyday", "woman-sewing-lamp", "a woman sewing by the light of an oil lamp"),
    ("everyday", "milkmaid-cows", "a milkmaid with a pail walking past cows at dawn"),
    ("everyday", "man-shaving-barber", "a barber shaving a customer in a striped chair"),
    ("everyday", "woman-piano-parlour", "a woman playing an upright piano in a parlour"),
    ("everyday", "fishermen-mending-nets", "fishermen mending nets on a quay"),
    ("everyday", "children-feeding-ducks", "two children feeding ducks at a pond"),
    ("everyday", "woman-letter-writing", "a woman writing a letter at a desk with a quill and inkwell"),
    ("everyday", "gardener-wheelbarrow", "a gardener pushing a wheelbarrow full of pumpkins"),
    ("everyday", "breakfast-croissants", "a breakfast table with croissants, a coffee pot and a bowl of fruit"),
    # ---- travel and destinations (18) ----
    ("travel", "eiffel-tower-spring", "the Eiffel Tower seen from a chestnut-lined avenue in spring"),
    ("travel", "paris-bridge-seine", "a stone bridge over the Seine with Notre-Dame behind"),
    ("travel", "montmartre-windmill", "a windmill on a hill in Montmartre with steps leading up"),
    ("travel", "riviera-promenade-palms", "a seaside promenade with palm trees and a turquoise bay"),
    ("travel", "monaco-harbour-cliffs", "a harbour with yachts below cliffs and pastel villas"),
    ("travel", "alps-chalet-meadow", "a wooden chalet in an alpine meadow with wildflowers and snowy peaks"),
    ("travel", "matterhorn-climbers", "two climbers with ropes and ice axes below a sharp snowy peak"),
    ("travel", "seaside-bathing-huts", "striped bathing huts on a sandy beach with a pier"),
    ("travel", "venice-gondola-canal", "a gondola on a narrow canal in Venice with a small bridge"),
    ("travel", "venice-san-marco-pigeons", "a piazza with a domed basilica and pigeons taking flight"),
    ("travel", "normandy-cliffs-arch", "a natural stone arch in white cliffs over the sea in Normandy"),
    ("travel", "normandy-timber-houses", "half-timbered houses along a harbour in Normandy"),
    ("travel", "spa-town-pump-room", "ladies with parasols beside a fountain in a spa garden"),
    ("travel", "orient-express-dining-car", "a luxurious dining car with white tablecloths and brass lamps"),
    ("travel", "orient-express-platform-night", "a sleeping-car train at a platform at night, steam rising"),
    ("travel", "mont-saint-michel-tide", "an abbey on a rocky island surrounded by the sea at high tide"),
    ("travel", "loire-chateau-gardens", "a château with turrets and formal gardens"),
    ("travel", "brittany-harbour-fishwives", "a Breton harbour with women in white lace headdresses"),
    # ---- fun (16) ----
    ("fun", "carousel-night", "a carousel with painted horses lit up at night"),
    ("fun", "ferris-wheel-fair", "a giant ferris wheel at a fair with crowds below"),
    ("fun", "circus-ringmaster-elephant", "a circus ringmaster in a red coat beside an elephant"),
    ("fun", "trapeze-artists", "two trapeze artists flying under a circus tent"),
    ("fun", "clown-juggling", "a clown in a ruffled collar juggling colored balls"),
    ("fun", "cafe-terrace-evening", "a crowded café terrace with round tables and lanterns at dusk"),
    ("fun", "cancan-dancers", "a line of cancan dancers lifting their frilled skirts"),
    ("fun", "waltz-ballroom", "couples waltzing in a mirrored ballroom with chandeliers"),
    ("fun", "picnic-riverbank", "a picnic on a riverbank with a basket, a parasol and a rowing boat"),
    ("fun", "cycling-race-velodrome", "cyclists racing around a banked velodrome track"),
    ("fun", "tandem-bicycle-couple", "a man and a woman riding a tandem bicycle down a country lane"),
    ("fun", "bathers-beach-umbrellas", "bathers in striped swimsuits splashing in the sea"),
    ("fun", "puppet-show-children", "children watching a puppet show in a park"),
    ("fun", "fireworks-over-crowd", "fireworks bursting over a crowd in a park at night"),
    ("fun", "rowing-regatta", "a rowing regatta with narrow boats and cheering crowds on the bank"),
    ("fun", "masked-ball", "guests in masks and dominoes at a masked ball"),
    # ---- wine and vineyards (10) ----
    ("wine", "grape-harvest-baskets", "grape pickers with baskets in a vineyard at harvest"),
    ("wine", "vineyard-hillside-sunset", "rows of vines on a hillside at sunset"),
    ("wine", "wine-cellar-barrels", "a cellar with oak barrels and a man holding a candle"),
    ("wine", "champagne-bottle-glasses", "a bottle of champagne and two coupe glasses on a lace tablecloth"),
    ("wine", "grape-press-workers", "men working a wooden grape press"),
    ("wine", "vintner-tasting-glass", "a vintner holding a glass of red wine up to the light"),
    ("wine", "vineyard-chateau-autumn", "a vineyard in autumn colors with a château behind"),
    ("wine", "wine-cart-oxen", "a cart of grapes pulled by two oxen"),
    ("wine", "bunch-grapes-leaves", "a bunch of purple grapes with vine leaves"),
    ("wine", "village-wine-festival", "villagers dancing around barrels at a wine festival"),
    # ---- boats (8) ----
    ("boats", "rowboat-lily-pond", "a rowing boat among water lilies"),
    ("boats", "steamboat-river-paddle", "a paddle steamer on a wide river"),
    ("boats", "fishing-boats-harbour-dawn", "fishing boats with red sails at dawn in a harbour"),
    ("boats", "canoe-mountain-lake", "a canoe on a mountain lake"),
    ("boats", "ferry-crossing-passengers", "a small ferry crossing a river with passengers under parasols"),
    ("boats", "ocean-liner-departure", "a great ocean liner leaving port with streamers and a waving crowd"),
    ("boats", "barge-canal-horse", "a canal barge pulled by a horse along a towpath"),
    ("boats", "motor-launch-lake", "a varnished motor launch speeding across a lake"),
    # ---- lighthouses (7) ----
    ("lighthouses", "lighthouse-storm-waves", "a lighthouse in a storm with waves breaking around it"),
    ("lighthouses", "lighthouse-beam-night", "a lighthouse beam sweeping over a calm sea at night"),
    ("lighthouses", "lighthouse-red-white-stripes", "a red and white striped lighthouse on a headland"),
    ("lighthouses", "lighthouse-keeper-lamp", "a lighthouse keeper polishing the great lamp"),
    ("lighthouses", "lighthouse-sunset-gulls", "a lighthouse on a cliff at sunset with gulls"),
    ("lighthouses", "lighthouse-island-boat", "a lighthouse on a small rocky island with a boat approaching"),
    ("lighthouses", "lighthouse-dunes", "a lighthouse behind sand dunes and sea grass"),
    # ---- sailing ships (8) ----
    ("sailing", "clipper-full-sail", "a tall clipper ship under full sail on the open sea"),
    ("sailing", "schooner-moonlight", "a two-masted schooner in moonlight"),
    ("sailing", "yacht-race-regatta", "yachts racing with white sails leaning in the wind"),
    ("sailing", "barque-harbour-dock", "a sailing ship tied up at a dock with sailors unloading crates"),
    ("sailing", "fishing-smack-brown-sails", "a fishing boat with brown sails in a choppy sea"),
    ("sailing", "tall-ship-sunset", "a tall ship silhouetted against an orange sunset"),
    ("sailing", "sailboat-children-pond", "a boy sailing a toy boat on a park pond"),
    ("sailing", "frigate-cannons-waves", "an old warship with rows of cannon ports cutting through waves"),
    # ---- trains and railway stations (10) ----
    ("trains", "locomotive-steam-platform", "a black steam locomotive at a station platform with steam rising"),
    ("trains", "station-glass-roof-crowd", "a railway station under a great glass roof with travelers and porters"),
    ("trains", "train-viaduct-valley", "a train crossing a tall stone viaduct over a valley"),
    ("trains", "train-mountain-tunnel", "a train emerging from a mountain tunnel into snow"),
    ("trains", "woman-waving-train-window", "a woman waving a handkerchief from a train window"),
    ("trains", "porter-luggage-trolley", "a porter pushing a trolley stacked with trunks and hatboxes"),
    ("trains", "train-coast-cliffs", "a train running along a coastal cliff above the sea"),
    ("trains", "station-clock-couple", "a couple embracing under a large station clock"),
    ("trains", "railway-night-signals", "a locomotive at night with glowing red and green signal lamps"),
    ("trains", "funicular-mountain", "a funicular railway climbing a steep mountainside"),
    # ---- old-time aeroplanes (7) ----
    ("aeroplanes", "biplane-over-fields", "a biplane flying over patchwork fields"),
    ("aeroplanes", "monoplane-channel-cliffs", "an early monoplane crossing the sea above white cliffs"),
    ("aeroplanes", "aviator-goggles-scarf", "an aviator in a leather helmet, goggles and a white scarf beside a biplane"),
    ("aeroplanes", "aeroplane-crowd-airfield", "a crowd watching a biplane take off from a grass airfield"),
    ("aeroplanes", "biplane-loop-sky", "a biplane looping the loop high above a town"),
    ("aeroplanes", "seaplane-harbour", "a seaplane on floats taxiing in a harbour"),
    ("aeroplanes", "biplane-sunset-clouds", "a biplane among pink clouds at sunset"),
    # ---- dirigibles and balloons (8) ----
    ("balloons", "hot-air-balloon-rooftops", "a striped hot-air balloon rising over city rooftops"),
    ("balloons", "balloon-festival-sky", "many colorful hot-air balloons filling the sky over a meadow"),
    ("balloons", "dirigible-over-eiffel", "a long silver airship flying past the Eiffel Tower"),
    ("balloons", "airship-hangar-crowd", "a great airship emerging from its hangar before a crowd"),
    ("balloons", "balloon-basket-couple", "a couple waving from the basket of a hot-air balloon"),
    ("balloons", "airship-over-sea-liner", "an airship flying over an ocean liner at sea"),
    ("balloons", "balloon-night-lanterns", "a hot-air balloon at night lit by paper lanterns"),
    ("balloons", "balloon-mountains-clouds", "a hot-air balloon drifting among mountain peaks and clouds"),
    # ---- jazz clubs and cabarets (10) ----
    ("cabaret", "jazz-trumpeter-spotlight", "a jazz trumpeter in a spotlight on a small stage"),
    ("cabaret", "jazz-band-saxophone-drums", "a jazz band with saxophone, double bass and drums"),
    ("cabaret", "cabaret-singer-red-dress", "a cabaret singer in a red dress at a microphone with a piano behind"),
    ("cabaret", "cabaret-chorus-feathers", "a chorus line in feathered headdresses on stage"),
    ("cabaret", "nightclub-dancing-couples", "couples dancing in a smoky nightclub under colored lights"),
    ("cabaret", "pianist-cabaret-candles", "a pianist at a grand piano in a candlelit cabaret"),
    ("cabaret", "cabaret-entrance-night", "the glowing entrance of a cabaret on a rainy night with a doorman"),
    ("cabaret", "clarinet-player-dancer", "a clarinet player and a dancer in a short fringed dress"),
    ("cabaret", "cabaret-audience-tables", "an audience at candlelit tables watching a stage show"),
    ("cabaret", "banjo-player-bar", "a banjo player on a stool at a crowded bar"),
    # ---- animals (7) ----
    ("animals", "black-cat-red-cushion", "a black cat sitting on a red cushion"),
    ("animals", "peacock-garden", "a peacock with its tail spread in a garden"),
    ("animals", "white-horse-meadow", "a white horse galloping through a meadow"),
    ("animals", "rooster-farmyard", "a proud rooster in a farmyard"),
    ("animals", "poodle-bow-chair", "a white poodle with a bow sitting on a velvet chair"),
    ("animals", "swans-pond-willow", "two swans on a pond beneath a willow"),
    ("animals", "fox-snowy-woods", "a red fox in snowy woods"),
    # ---- flowers (6) ----
    ("flowers", "irises-vase", "purple irises in a tall vase"),
    ("flowers", "poppies-field-red", "a field of red poppies under a blue sky"),
    ("flowers", "roses-bouquet-ribbon", "a bouquet of pink roses tied with a ribbon"),
    ("flowers", "water-lilies-pond", "water lilies on a still pond"),
    ("flowers", "chrysanthemums-window", "yellow chrysanthemums in a pot on a windowsill"),
    ("flowers", "wisteria-arbour", "a wisteria arbour in full bloom"),
    # ---- motor cars (6) ----
    ("motorcars", "open-touring-car-couple", "a couple in dusters and goggles in an open touring car on a country road"),
    ("motorcars", "motor-car-race-dust", "early racing cars speeding past a crowd in a cloud of dust"),
    ("motorcars", "chauffeur-limousine-lady", "a chauffeur holding the door of a limousine for a lady in furs"),
    ("motorcars", "motor-car-mountain-pass", "an early motor car climbing a mountain pass"),
    ("motorcars", "motor-car-seaside-road", "a red motor car on a coastal road above the sea"),
    ("motorcars", "motor-car-breakdown-countryside", "a man in goggles cranking a stalled motor car while a woman waits under a parasol"),
    # ---- winter sports (7) ----
    ("winter", "skier-alpine-slope", "a skier in a wool sweater speeding down an alpine slope"),
    ("winter", "ice-skaters-frozen-lake", "ice skaters in long coats on a frozen lake"),
    ("winter", "bobsleigh-team-run", "a bobsleigh team racing down an icy run"),
    ("winter", "sledging-children-hill", "children sledging down a snowy hill"),
    ("winter", "skating-couple-muff", "a couple skating arm in arm, the woman with a fur muff"),
    ("winter", "snowshoes-pine-forest", "a hiker on snowshoes in a snowy pine forest"),
    ("winter", "ski-jumper-mountains", "a ski jumper soaring above snowy mountains"),
    # ---- markets (6) ----
    ("markets", "flower-market-stalls", "a flower market with stalls of tulips and roses"),
    ("markets", "fish-market-quay", "a fish market on a quay with baskets of fish and oysters"),
    ("markets", "fruit-market-apples-pears", "a market stall piled with apples, pears and grapes"),
    ("markets", "christmas-market-snow", "a snowy evening market with lanterns and steaming stalls"),
    ("markets", "cheese-market-wheels", "a cheese market with great wheels of cheese on a cart"),
    ("markets", "covered-market-hall", "a covered market hall with iron columns and busy shoppers"),
]

PREFIX = "belleposter, Belle Epoque lithograph poster, "
NEG = "photograph, photo, 3d render, blurry, watermark, text, lettering, words, caption, title, modern, gradient"


def ordered():
    """Round-robin across categories so consecutive showcase days differ in subject."""
    by = defaultdict(list)
    cats = []
    for c, s, cap in ROWS:
        if c not in cats:
            cats.append(c)
        by[c].append((c, s, cap))
    out = []
    while any(by[c] for c in cats):
        for c in cats:
            if by[c]:
                out.append(by[c].pop(0))
    return out


def main():
    assert len(ROWS) == 180, len(ROWS)
    slugs = [s for _, s, _ in ROWS]
    assert len(set(slugs)) == 180, "duplicate slug"
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(os.path.dirname(here), "showcase", "x180", "captions.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for i, (c, s, cap) in enumerate(ordered(), 1):
            f.write(json.dumps({"number": i, "slug": s, "category": c, "caption": cap,
                                "prompt": PREFIX + cap, "negative": NEG}, ensure_ascii=False) + "\n")
    print("wrote", out, 180, "rows;", len({c for c, _, _ in ROWS}), "categories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
