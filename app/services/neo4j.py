"""
Neo4j 知识图谱连接器（当前为桩代码，使用 MySQL 替代）。

启用方式：
1. 安装 pip install neo4j
2. 在 .env 配置：
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=bytesavor
3. 重启服务，知识检索自动切换到 Neo4j

基于架构图中的 FoodKG 知识图谱：
- 食材关系：鸡胸肉 → 高蛋白 → 适合减脂 → 与西兰花搭配
- 用于 Y-决策阶段的关系推理
"""


class Neo4jFoodKG:
    """FoodKG 知识图谱查询封装（当前未启用，使用 MySQL 替代）"""

    def __init__(self, uri: str = "", user: str = "", password: str = ""):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver = None

    async def connect(self):
        """建立 Neo4j 连接（延迟初始化）"""
        try:
            from neo4j import AsyncGraphDatabase
            self._driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
        except ImportError:
            pass  # neo4j 未安装，走 MySQL fallback

    async def query_food_relations(self, ingredient: str) -> list[dict]:
        """查询食材的营养关系和搭配建议"""
        if not self._driver:
            return []
        query = """
        MATCH (f:Food {name: $name})-[r]->(related)
        RETURN type(r) as relation, related.name as target, related.properties as props
        LIMIT 10
        """
        async with self._driver.session() as session:
            result = await session.run(query, name=ingredient)
            return [dict(record) for record in await result.data()]

    async def find_recipes_by_ingredients(self, ingredients: list[str]) -> list[dict]:
        """根据食材列表查找可做的菜谱"""
        if not self._driver:
            return []
        query = """
        MATCH (r:Recipe)-[:REQUIRES]->(f:Food)
        WHERE f.name IN $names
        WITH r, count(DISTINCT f) as matched_count
        ORDER BY matched_count DESC
        RETURN r.name as title, r.id as recipe_id, matched_count
        LIMIT 10
        """
        async with self._driver.session() as session:
            result = await session.run(query, names=ingredients)
            return [dict(record) for record in await result.data()]


# 全局实例（默认不连接，走 MySQL fallback）
food_kg = Neo4jFoodKG()
