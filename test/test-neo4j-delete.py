from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv('.env', override=True)
# 连接配置（替换为您的AuraDB信息）
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session() as session:
        # 1. 删除所有节点和关系
        session.run("""
        MATCH (n)
        CALL {
            WITH n
            DETACH DELETE n
        } IN TRANSACTIONS OF 10000 ROWS
        """)
        print("✅ 所有节点和关系已删除")
        
        # 2. 删除所有约束（使用兼容语法）
        try:
            session.run("""
            CALL db.constraints() YIELD name
            CALL {
                WITH name
                DROP CONSTRAINT $name
            } IN TRANSACTIONS
            """)
            print("✅ 所有约束已删除")
        except Exception as e:
            print(f"⚠️  删除约束时出错: {e}")
        
        # 3. 删除所有索引（使用兼容语法）
        try:
            session.run("""
            CALL db.indexes() YIELD name
            CALL {
                WITH name
                DROP INDEX $name
            } IN TRANSACTIONS
            """)
            print("✅ 所有索引已删除")
        except Exception as e:
            print(f"⚠️  删除索引时出错: {e}")
        
        # 4. 验证清理结果
        result = session.run("MATCH (n) RETURN count(n) as nodeCount")
        node_count = result.single()["nodeCount"]
        
        print(f"📊 清理后统计:")
        print(f"   节点数量: {node_count}")
        
        # 验证所有label是否也都被删除
        try:
            result = session.run("CALL db.labels() YIELD label RETURN label")
            labels = [record["label"] for record in result]
            print(f"   Label数量: {len(labels)}")
            if labels:
                print(f"   Label列表: {labels}")
            else:
                print("   没有剩余的label，所有label已被删除。")
        except Exception as e:
            print(f"   无法获取label信息: {e}")

        
        # 尝试获取约束和索引信息
        try:
            result = session.run("CALL db.constraints() YIELD name")
            constraints = list(result)
            print(f"   约束数量: {len(constraints)}")
            if constraints:
                print(f"   约束列表: {[c['name'] for c in constraints]}")
        except Exception as e:
            print(f"   无法获取约束信息: {e}")
            constraints = []
        
        try:
            result = session.run("CALL db.indexes() YIELD name")
            indexes = list(result)
            print(f"   索引数量: {len(indexes)}")
            if indexes:
                print(f"   索引列表: {[i['name'] for i in indexes]}")
        except Exception as e:
            print(f"   无法获取索引信息: {e}")
            indexes = []
        
        if node_count == 0:
            print("🎉 数据库数据已完全清理！")
        else:
            print("⚠️  数据库可能还有残留数据")