"""食材品质评估 —— VLM视觉 + 挑选知识库"""

from app.services.vlm import analyze_food
from app.services.ingredient_tips import get_tip


QUALITY_STANDARDS = {
    "番茄": {"优": "色泽鲜红均匀、果形圆润饱满、果蒂翠绿、触感微软有弹性、无裂痕虫眼",
             "中": "颜色偏橙或偏青、果形稍不规整",
             "差": "有裂口、软烂、发霉、果蒂干枯发黑"},
    "西红柿": {"优": "色泽鲜红均匀、果形圆润饱满、果蒂翠绿、触感微软有弹性、无裂痕虫眼",
              "中": "颜色偏橙或偏青、果形稍不规整",
              "差": "有裂口、软烂、发霉、果蒂干枯发黑"},
    "西瓜": {"优": "拍打听声清脆、瓜脐小而凹、瓜藤翠绿卷曲、纹路清晰、同等大小较重",
             "中": "声音偏闷、纹路模糊、瓜藤干枯",
             "差": "有裂口、软斑、异味、拍打声音空洞"},
    "榴莲": {"优": "浓郁香味、果刺大而疏、底部有裂缝、摇晃有果肉晃动感、果壳金黄",
             "中": "香味较淡、果壳青色需放置、果刺较密",
             "差": "无香味或有酒精发酵味、果壳发黑、裂缝过大露出果肉"},
}


async def assess(image_data: str) -> dict:
    """评估图片中食材的品质"""
    result = await analyze_food(image_data)
    if not result or not result.get("ingredients"):
        return {"status": "no_food", "message": "未识别到食材"}

    items = []
    for ing in result["ingredients"]:
        name = ing["name"]
        freshness = ing.get("freshness", "medium")
        features = ing.get("features", "")
        tip = get_tip(name)

        # 判断品质等级
        if freshness == "high":
            grade, grade_text = "优", "品质优良，推荐购买"
        elif freshness == "medium":
            grade, grade_text = "中", "品质一般，可以购买"
        else:
            grade, grade_text = "差", "不建议购买"

        standard = QUALITY_STANDARDS.get(name, {})
        items.append({
            "name": name,
            "freshness": freshness,
            "grade": grade,
            "grade_text": grade_text,
            "features": features,
            "standard": standard.get(grade, tip),
            "tip": tip,
        })

    return {
        "status": "ok",
        "items": items,
        "portion_estimation": result.get("portion_estimation", {}),
    }
