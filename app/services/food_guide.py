"""探店美食向导 —— VLM识别菜品 + 文化故事"""

from app.services.vlm import analyze_food
from app.services.vlm.prompts import DISH_UNDERSTAND

GUIDE_PROMPT = """你是专业美食向导。识别图中菜品，给出完整解析。返回JSON:
{
  "dish_name": "菜品名",
  "cuisine": "菜系(粤菜/川菜/鲁菜/苏菜/浙菜/闽菜/湘菜/徽菜/其他)",
  "category": "分类(荤菜/素菜/汤羹/面点/小吃)",
  "history": "这道菜的历史渊源和文化故事(80-150字)",
  "features": "口味特点和烹饪技法(30-50字)",
  "best_eat": "最佳吃法和搭配建议(30-50字)",
  "ingredients": [{"name": "主要食材", "amount": "用量"}],
  "estimated_calories": 500,
  "difficulty": "简单/中等/困难"
}"""

# 经典菜品知识库（补充VLM可能不知道的细节）
CLASSIC_DISHES = {
    "白切鸡": {"cuisine": "粤菜", "history": "白切鸡是粤菜'无鸡不成宴'的代表，起源于清代广州。讲究'浸'而非'煮'，用90℃虾眼水反复浸烫，皮爽肉滑骨中带血是为上品。广东人待客必上白切鸡，是对客人最高的尊重。", "features": "皮爽肉滑、原汁原味，蘸姜葱蓉或沙姜酱油", "best_eat": "蘸姜葱蓉，配一碗鸡油饭，先吃皮再吃肉"},
    "烤鸭": {"cuisine": "京菜", "history": "北京烤鸭起源于南北朝，明代成为宫廷御膳。全聚德创立于1864年，采用挂炉明火果木烤制。片鸭讲究108片，片片带皮带肉。", "features": "皮脆肉嫩、色泽红亮，果木熏香渗入鸭肉", "best_eat": "薄饼卷鸭皮+甜面酱+葱丝+黄瓜条，先吃皮后吃肉"},
    "东坡肉": {"cuisine": "浙菜", "history": "苏轼贬谪黄州时发明，他在《猪肉颂》中写道'黄州好猪肉，价贱如泥土。贵者不肯吃，贫者不解煮'。以少水慢火炖出'酥烂而形不碎'的绝妙口感，是中国文人菜的代表。", "features": "色如玛瑙、肥而不腻、酥烂入味，酒香浓郁", "best_eat": "配白米饭，一勺肉汁拌饭是灵魂吃法"},
    "麻婆豆腐": {"cuisine": "川菜", "history": "创于清同治年间成都万福桥畔陈氏饭铺。老板娘脸上有麻子，人称'陈麻婆'。她创制的豆腐麻、辣、烫、香、酥、嫩、鲜、活八字俱全，流传至今150余年。", "features": "麻辣烫香，牛肉末酥香，豆腐嫩滑，花椒是灵魂", "best_eat": "趁热吃，拌饭一绝，第一口先感受花椒的麻"},
    "佛跳墙": {"cuisine": "闽菜", "history": "清光绪年间福州聚春园郑春发创制。一坛煨制，坛启时荤香四溢，秀才吟诗'坛启荤香飘四邻，佛闻弃禅跳墙来'，故得名。以鲍鱼海参鱼翅等三十余种原料慢火煨制十几小时。", "features": "汤浓味醇、荤香四溢，几十种山珍海味精华融于一坛", "best_eat": "先品汤再吃料，从清淡到浓郁依次品尝"},
    "宫保鸡丁": {"cuisine": "川菜", "history": "清代四川总督丁宝桢(宫保是他的荣誉衔)家厨所创。丁宝桢爱吃鸡丁，家厨用花生米干辣椒花椒烹制，后传入民间。此菜在海外知名度极高，英文名Kung Pao Chicken。", "features": "糊辣味型，荔枝口，酸甜咸鲜辣交织，花生酥脆", "best_eat": "配白米饭，花生米和鸡丁一起吃口感最好"},
    "清蒸鲈鱼": {"cuisine": "粤菜", "history": "粤菜'鸡有鸡味，鱼有鱼味'哲学的极致体现。只用姜葱酱油，八分钟精准蒸制，不掩食材本味。广东人评价一道清蒸鱼的标准是'骨肉分离、皮不破、肉不老、汁不咸'。", "features": "原汁原味、肉质鲜嫩、葱油提鲜，酱油回甘", "best_eat": "先吃鱼颊肉(最嫩部位)，再吃鱼肚，蘸蒸鱼汁"},
    "水煮鱼": {"cuisine": "川菜", "history": "虽名'水煮'实为'油浸'。起源于重庆江北，本是渔夫船上用江水煮鱼的粗犷做法，后经改良成为川菜名品。1990年代在北京上海引爆川菜热潮。", "features": "鱼片嫩滑、麻辣鲜香、油而不腻，辣椒花椒浮满汤面", "best_eat": "夹鱼片沥去表面油，蘸醋解腻，配冰啤酒是经典搭配"},
}


async def guide(image_data: str) -> dict:
    """识别菜品并返回美食向导解析"""
    result = await analyze_food(image_data, DISH_UNDERSTAND)
    if not result:
        return {"status": "no_dish", "message": "未能识别图中菜品"}

    dish_name = result.get("dish_name", "")

    # 查找经典菜知识库
    classic = {}
    for key, info in CLASSIC_DISHES.items():
        if key in dish_name or dish_name in key:
            classic = info
            break

    return {
        "status": "ok",
        "dish_name": dish_name,
        "cuisine": classic.get("cuisine", result.get("cuisine", "")),
        "category": result.get("category", ""),
        "history": classic.get("history", result.get("history", "")),
        "features": classic.get("features", result.get("features", "")),
        "best_eat": classic.get("best_eat", result.get("best_eat", "")),
        "ingredients": result.get("ingredients", []),
        "estimated_calories": result.get("estimated_calories", 0),
        "difficulty": result.get("difficulty", ""),
        "from_knowledge_base": bool(classic),
    }
