"""Pagouro BE showcase, jigsaw batch 1 (2026-10-04): captions for new Pagouro Jigsaw pictures.

Themes asked for by Eric: Paris, nightlife, flowers, boats, gardens, people strolling, cycling, dancing,
landscapes of Europe, salons, castles, sailing and steamships, scientific labs, libraries, airships.
No words in any picture; faces must be right. Captions name no living person and no trademark, and keep
clear of drinking and smoking (the game's content rating says none).

    python scripts/showcase_jigsaw_b1_prompts.py  ->  showcase/jigsaw_b1/captions.jsonl
Each row: number, slug, category, caption, prompt, negative, people (True gets 12 seeds, else 8).
"""
import io, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "showcase", "jigsaw_b1")
PREFIX = "belleposter, Belle Epoque lithograph poster, "
NEGATIVE = ("photograph, photo, 3d render, blurry, watermark, text, lettering, words, caption, title, modern, "
            "gradient, deformed face, distorted face, asymmetrical eyes, extra fingers, extra limbs, "
            "cigarette, smoking, wine glass, bottle")

# (category, people?, caption)
P, N = True, False
CAPTIONS = [
    ("paris", N, "the Eiffel Tower at dusk seen across the Seine, gas lamps glowing along the quay"),
    ("paris", N, "the domes of Sacré-Cœur on Montmartre hill above Paris rooftops in morning light"),
    ("paris", N, "a Paris boulevard in the rain with horse-drawn cabs and rows of chestnut trees"),
    ("paris", P, "a flower seller with her cart of roses on a Paris street corner, smiling"),
    ("paris", N, "bookstalls along the Seine under plane trees, Notre-Dame in the distance"),
    ("paris", N, "the glass roof of a grand Paris railway station with steam rising in sunlight"),
    ("paris", N, "the Arc de Triomphe at sunset with carriages circling around it"),
    ("paris", P, "a young woman in a feathered hat at the window of a Paris balcony overlooking rooftops"),
    ("paris", N, "the Pont Alexandre III bridge with golden statues over the Seine"),
    ("paris", N, "a Paris street of shop awnings and lamp posts on a snowy winter evening"),
    ("nightlife", P, "dancers in swirling skirts on a cabaret stage under bright footlights"),
    ("nightlife", N, "a carousel lit with lanterns at a night fair, painted horses mid-turn"),
    ("nightlife", N, "an opera house facade glowing at night with carriages arriving"),
    ("nightlife", P, "a violinist in evening dress playing under a single stage spotlight"),
    ("nightlife", N, "paper lanterns strung over an outdoor dance floor in a summer garden at night"),
    ("nightlife", N, "a theatre interior with red velvet seats, gilded balconies and a glowing chandelier"),
    ("nightlife", P, "a clown juggling colored balls in a circus ring under a striped tent"),
    ("nightlife", N, "fireworks bursting over a river with boats lit by lanterns"),
    ("nightlife", P, "a woman in a long sequined gown singing on stage, arms open"),
    ("nightlife", N, "a moonlit city square with glowing cafe windows and gas lamps"),
    ("flowers", N, "a tall bouquet of pink peonies in a blue porcelain vase"),
    ("flowers", N, "red poppies and blue cornflowers in a wheat field under a summer sky"),
    ("flowers", N, "a wreath of white roses and ivy on a dark green background"),
    ("flowers", N, "yellow daffodils and tulips in a terracotta pot on a windowsill"),
    ("flowers", N, "a branch of pink cherry blossom against a pale blue sky"),
    ("flowers", N, "purple lilacs in a glass vase beside an open window"),
    ("flowers", N, "a field of lavender rows leading to a stone farmhouse"),
    ("flowers", N, "orange marigolds and blue delphiniums in a cottage border"),
    ("flowers", N, "a single white lily in an art nouveau frame of curling stems"),
    ("flowers", N, "a basket of wildflowers on a wooden table in sunlight"),
    ("boats", N, "fishing boats with red sails drawn up on a pebble beach"),
    ("boats", P, "a man in a straw boater hat rowing a small boat on a calm river"),
    ("boats", N, "a harbor of colorful fishing boats below a hillside village"),
    ("boats", N, "a paddle steamer on a wide river with green hills behind"),
    ("boats", N, "rowing boats tied to a wooden jetty on a misty lake at dawn"),
    ("boats", N, "a canal barge with flower boxes passing under a stone bridge"),
    ("boats", P, "two women in white dresses in a punt on a river under willow trees"),
    ("boats", N, "a lifeboat launching into rough surf from a slipway"),
    ("gardens", N, "a formal French garden with clipped hedges, gravel paths and a round fountain"),
    ("gardens", N, "a rose garden archway leading to a white gazebo"),
    ("gardens", P, "a gardener in an apron pushing a wheelbarrow of flowers along a garden path"),
    ("gardens", N, "a glass greenhouse full of palms and ferns in a botanical garden"),
    ("gardens", N, "a Japanese-style garden with a red bridge over a pond of water lilies"),
    ("gardens", N, "a kitchen garden with rows of vegetables and a brick wall with pear trees"),
    ("gardens", N, "a park bench under a flowering chestnut tree beside a pond with ducks"),
    ("gardens", N, "a topiary garden with hedges clipped into spirals and birds"),
    ("gardens", P, "a girl with a watering can among sunflowers in a summer garden"),
    ("gardens", N, "a stone terrace with urns of geraniums overlooking a lake"),
    ("strolling", P, "a couple strolling arm in arm along a seaside promenade with parasols"),
    ("strolling", P, "a woman in a long coat and fur hat walking a poodle in a snowy park"),
    ("strolling", P, "families strolling in a sunny park among trees and flower beds"),
    ("strolling", P, "a gentleman in a top hat and a lady with a parasol walking along a riverbank"),
    ("strolling", P, "a mother and daughter in matching hats walking through a meadow of daisies"),
    ("strolling", P, "people strolling under umbrellas on a rainy boulevard, seen from behind"),
    ("strolling", P, "a woman in a striped dress walking on a beach boardwalk with a hat in her hand"),
    ("strolling", P, "two friends walking along a country lane with a dog"),
    ("strolling", P, "a lady walking down a grand staircase in a flowing evening gown"),
    ("strolling", P, "children rolling hoops along a park path"),
    ("cycling", P, "a woman in bloomers riding a bicycle along a country road"),
    ("cycling", P, "a racing cyclist leaning into a turn on a velodrome track"),
    ("cycling", P, "a young man on a high-wheel penny-farthing bicycle in a park"),
    ("cycling", P, "a group of cyclists riding past poplar trees on a sunny road"),
    ("cycling", P, "a woman cycling with a basket of flowers on the handlebars"),
    ("cycling", P, "a couple riding a tandem bicycle through a village"),
    ("cycling", P, "a postman cycling past a field of sunflowers"),
    ("cycling", P, "a girl walking her bicycle up a hill road above the sea"),
    ("dancing", P, "a couple waltzing in a ballroom under crystal chandeliers"),
    ("dancing", P, "a ballerina in a white tutu on pointe, arms raised"),
    ("dancing", P, "villagers dancing in a circle at a summer fete with musicians"),
    ("dancing", P, "a woman dancing with long flowing veils of colored silk"),
    ("dancing", P, "a tango couple in an elegant pose on a dark stage"),
    ("dancing", P, "children dancing around a maypole with ribbons"),
    ("dancing", P, "a flamenco dancer in a red ruffled dress with a fan"),
    ("dancing", P, "couples dancing on a riverside open-air dance floor on a Sunday afternoon"),
    ("landscapes", N, "the Matterhorn above an alpine meadow of wildflowers"),
    ("landscapes", N, "a Tuscan hill town with cypress trees and golden fields"),
    ("landscapes", N, "the white cliffs and blue sea of the Amalfi coast with a village on the slope"),
    ("landscapes", N, "a Norwegian fjord with steep green mountains and a small red boathouse"),
    ("landscapes", N, "Scottish highlands with purple heather and a loch under clouds"),
    ("landscapes", N, "a Dutch polder with a canal, windmills and grazing cows"),
    ("landscapes", N, "a Greek island village of white houses and blue domes above the sea"),
    ("landscapes", N, "the Danube winding through a valley with a monastery on a hill"),
    ("landscapes", N, "a Provence village on a hilltop above olive groves"),
    ("landscapes", N, "snowy peaks of the Dolomites reflected in a green lake"),
    ("landscapes", N, "an Irish coastline of green fields and stone walls above the Atlantic"),
    ("landscapes", N, "a Black Forest valley with a timbered farmhouse and pine trees"),
    ("salons", P, "a pianist playing a grand piano in an elegant drawing room with guests listening"),
    ("salons", P, "ladies in long gowns conversing in a gilded salon with tall mirrors"),
    ("salons", N, "an elegant drawing room with silk sofas, a marble fireplace and a vase of roses"),
    ("salons", P, "a painter at an easel in a sunlit studio with canvases on the walls"),
    ("salons", P, "a string quartet playing in a candlelit salon"),
    ("salons", P, "a woman reading a letter on a chaise longue by a tall window"),
    ("salons", N, "a tea table set with porcelain cups, cakes and flowers in a parlor"),
    ("salons", P, "a poet reading aloud to friends gathered in a salon"),
    ("castles", N, "a fairy-tale castle with white towers on a forested mountain ridge"),
    ("castles", N, "a Loire chateau reflected in a river with arches"),
    ("castles", N, "a ruined castle on a crag above a river valley at sunset"),
    ("castles", N, "a castle on a rocky island reached by a causeway"),
    ("castles", N, "a moated castle with round towers and a drawbridge in spring"),
    ("castles", N, "a Rhine castle above vineyards and a river with a paddle steamer"),
    ("castles", N, "a Scottish castle on a loch shore with mountains behind"),
    ("castles", N, "a snowy castle with lit windows on a winter night"),
    ("sailing", N, "a racing yacht heeling under full white sails on a blue sea"),
    ("sailing", N, "an ocean liner with four funnels steaming out of harbor, gulls above"),
    ("sailing", N, "a three-masted sailing ship at anchor in a calm bay at sunset"),
    ("sailing", N, "a regatta of small sailboats with colored sails on a lake"),
    ("sailing", N, "a paddle steamer on a lake with mountains behind"),
    ("sailing", N, "a steamship deck with deck chairs and lifebuoys facing the open sea"),
    ("sailing", N, "a tall ship sailing through stormy waves"),
    ("sailing", N, "a steam yacht moored in a Riviera harbor with palm trees"),
    ("labs", P, "a scientist in a white coat examining a glowing glass flask in a laboratory"),
    ("labs", N, "a laboratory bench crowded with glass flasks, coils and brass instruments"),
    ("labs", P, "an astronomer looking through a large brass telescope in an observatory dome"),
    ("labs", N, "an electrical laboratory with crackling sparks between brass spheres"),
    ("labs", P, "a woman chemist pouring a colored liquid between glass tubes"),
    ("labs", N, "a cabinet of curiosities with butterflies, shells and fossils"),
    ("labs", P, "a botanist sketching plants beside a microscope"),
    ("labs", N, "a brass microscope and glass slides on a wooden desk by a window"),
    ("libraries", N, "a grand library with tall wooden bookshelves, ladders and a glass dome"),
    ("libraries", P, "a young woman reading at a long library table under green lamps"),
    ("libraries", N, "a spiral staircase in a library lined with books"),
    ("libraries", N, "stacks of old books, a globe and a candle on a scholar's desk"),
    ("libraries", P, "an old librarian with spectacles shelving books on a ladder"),
    ("libraries", N, "a reading room with arched windows and rows of desks in afternoon light"),
    ("libraries", P, "a child reading a picture book in a window seat"),
    ("libraries", N, "a bookshop window full of books and maps on a rainy street"),
    ("airships", N, "a silver airship floating over the rooftops of Paris"),
    ("airships", N, "an airship moored to a tall mast at dawn with tiny figures below"),
    ("airships", N, "an airship sailing above the Alps among white clouds"),
    ("airships", N, "an airship over a harbor full of steamships"),
    ("airships", P, "passengers waving from the gondola of an airship over the countryside"),
    ("airships", N, "an airship in a huge hangar with its doors open"),
    ("airships", N, "two airships crossing a sunset sky above a river city"),
    ("airships", N, "an airship flying over a castle on a hill"),
]


def slug(c):
    w = re.sub(r"[^a-z0-9 ]", "", c.lower().replace("é", "e").replace("œ", "oe")).split()
    stop = {"a", "an", "the", "of", "in", "on", "with", "and", "at", "by", "to", "over", "under", "above", "along",
            "through", "its", "from", "into", "past", "up", "down", "seen", "across", "between", "beside", "behind"}
    return "-".join([x for x in w if x not in stop][:4])


def main():
    os.makedirs(OUT, exist_ok=True)
    seen = set()
    with io.open(os.path.join(OUT, "captions.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for i, (cat, people, cap) in enumerate(CAPTIONS, 1):
            s = slug(cap)
            assert s not in seen, s
            seen.add(s)
            f.write(json.dumps({"number": i, "slug": s, "category": cat, "caption": cap, "prompt": PREFIX + cap,
                                "negative": NEGATIVE, "people": people}, ensure_ascii=False) + "\n")
    n_p = sum(1 for c in CAPTIONS if c[1])
    print(f"{len(CAPTIONS)} captions, {n_p} with people (12 seeds), {len(CAPTIONS) - n_p} without (8 seeds): "
          f"{n_p * 12 + (len(CAPTIONS) - n_p) * 8} pictures")


if __name__ == "__main__":
    main()
