import ast
import pandas as pd

from kg import get_kg

### Create graph nodes using text chunks
def create_node(kg, node_list_of_dicts, query):
    ### Loop through and create nodes for all cards
    node_count = 0
    for node_dict in node_list_of_dicts:
        # print(f"Creating `:Chunk` node for chunk ID {chunk['chunkId']}")
        kg.query(query, 
                params={
                    'params': node_dict
                })
        node_count += 1
    print(f"Created {node_count} nodes")

def create_card_node(kg, cards_list_of_dicts):
    merge_card_node_query = """
    MERGE(card:CARD {id: $params.id})
        ON CREATE SET 
            card.id = $params.id,
            card.name = $params.name
    RETURN card
    """
    create_node(kg, node_list_of_dicts=cards_list_of_dicts, query=merge_card_node_query)

def create_service_node(kg, services_list_of_dicts):
    merge_service_node_query = """
    MERGE(service:SERVICE {id: $params.id})
        ON CREATE SET 
            service.id = $params.id,
            service.name = $params.name
    RETURN service
    """
    create_node(kg, node_list_of_dicts=services_list_of_dicts, query=merge_service_node_query)

def create_footnote_node(kg, footnotes_list_of_dicts):
    merge_footnote_node_query = """
    MERGE(footnote:FOOTNOTE {id: $params.id})
        ON CREATE SET 
            footnote.id = $params.id,
            footnote.note = $params.note
    RETURN footnote
    """
    create_node(kg, node_list_of_dicts=footnotes_list_of_dicts, query=merge_footnote_node_query)

def create_fee_rule_node(kg, fee_rules_list_of_dicts):
    merge_fee_rule_node_query = """
    MERGE(fee_rule:FEE_RULE {id: $params.id})
        ON CREATE SET 
            fee_rule.id = $params.id,
            fee_rule.service_id = $params.service_id,
            fee_rule.service = $params.service,
            fee_rule.service_type = $params.service_type,
            fee_rule.description = $params.description
    RETURN fee_rule
    """
    create_node(kg, node_list_of_dicts=fee_rules_list_of_dicts, query=merge_fee_rule_node_query)


##### 建立关系
def create_relationship_card_to_service(kg):
    relationship_card_to_service_query = """
    MATCH
    (card:CARD),
    (service:SERVICE)
    MERGE (card)-[r:HAS_SERVICE]->(service)
    RETURN count(r)
    """
    result = kg.query(relationship_card_to_service_query)
    print("create {n} relationship card to service done".format(n=result[0]['count(r)']))

def create_relationship_service_to_fee_rule(kg):
    relationship_service_to_fee_rule_query = """
    MATCH
    (service:SERVICE),
    (fee_rule:FEE_RULE)
    WHERE fee_rule.service_id = service.id
    MERGE (service)-[r:HAS_FEE_RULE]->(fee_rule)
    RETURN count(r)
    """
    result = kg.query(relationship_service_to_fee_rule_query)
    print("create {n} relationship service to fee rule done".format(n=result[0]['count(r)']))



def create_relationship_fee_rule_to_footnote(kg, map_df):
    # relationship_fee_rule_to_footnote_query = """
    # MATCH
    # (service:SERVICE {id: $service_id}),
    # (fee_rule:FEE_RULE {id: $fee_rule_id}),
    # (footnote:FOOTNOTE {id: $footnote_id})
    # OPTIONAL MATCH (card:CARD {id: $card_id})
    # MERGE (fee_rule)-[r:HAS_FOOTNOTE]->(footnote)
    # RETURN count(r)
    # """


    # query_with_card_id = """
    # MATCH
    # (card:CARD {id: $card_id}),
    # (service:SERVICE {id: $service_id}),
    # (fee_rule:FEE_RULE {id: $fee_rule_id}),
    # (footnote:FOOTNOTE {id: $footnote_id})
    # MERGE (fee_rule)-[r:HAS_FOOTNOTE]->(footnote)
    # RETURN count(r)
    # """

    query_with_card_id = """
    MATCH (card:CARD {id: $card_id}),
    (footnote:FOOTNOTE {id: $footnote_id})
    MERGE (card)-[r:HAS_FOOTNOTE]->(footnote)
    RETURN count(r)
    """

    query_without_card_id = """
    MATCH
    (service:SERVICE {id: $service_id}),
    (fee_rule:FEE_RULE {id: $fee_rule_id}),
    (footnote:FOOTNOTE {id: $footnote_id})
    MERGE (fee_rule)-[r:HAS_FOOTNOTE]->(footnote)
    RETURN count(r)
    """
    #### test
    # params = {'card_id': None, 'service_id': 3, 'fee_rule_id': 7, 'footnote_id': 2}
    # result = kg.query(relationship_fee_rule_to_footnote_query, 
    #             params=params)
    # print("create {n} relationship fee rule to footnote done".format(n=result[0]['count(r)']))

    footnote_relationship_count = 0
    for i in map_df.index:
        card_id = None if pd.isna(map_df.loc[i, "card_id"]) else int(map_df.loc[i, "card_id"])
        service_id = None if pd.isna(map_df.loc[i, "service_id"]) else int(map_df.loc[i, "service_id"])
        fee_rule_id = None if pd.isna(map_df.loc[i, "fee_rule_id"]) else int(map_df.loc[i, "fee_rule_id"])
        note_ids_str = map_df.loc[i, "note_ids"]
        note_ids = ast.literal_eval(note_ids_str) if isinstance(note_ids_str, str) else note_ids_str
        for note_id in note_ids:
            if card_id is not None:
                result = kg.query(query_with_card_id, 
                        params={'card_id': card_id, 'footnote_id': note_id})
            else:
                result = kg.query(query_without_card_id, 
                        params={'service_id': service_id, 'fee_rule_id': fee_rule_id, 'footnote_id': note_id})
            footnote_relationship_count += result[0]['count(r)']
    print("create {n} relationship fee rule to footnote done".format(n=footnote_relationship_count))


def main():
    kg = get_kg()

    ### 是否需要重新创建一个index
    cards_df = pd.read_csv('./data/cards.csv', header=0)
    services_df = pd.read_csv('./data/services.csv', header=0)
    footnotes_df = pd.read_csv('./data/footnotes.csv', header=0)
    fee_rules_df = pd.read_csv('./data/fee_rules.csv', header=0)
    map_df = pd.read_csv('./data/map.csv', header=0)
    cards_list_of_dicts = cards_df.to_dict(orient='records')
    services_list_of_dicts = services_df.to_dict(orient='records')
    footnotes_list_of_dicts = footnotes_df.to_dict(orient='records')
    fee_rules_list_of_dicts = fee_rules_df.to_dict(orient='records')

    # create_card_node(kg, cards_list_of_dicts)
    # create_service_node(kg, services_list_of_dicts)
    # create_footnote_node(kg, footnotes_list_of_dicts)
    # create_fee_rule_node(kg, fee_rules_list_of_dicts)
    # create_relationship_card_to_service(kg)
    # create_relationship_service_to_fee_rule(kg)
    create_relationship_fee_rule_to_footnote(kg, map_df)


if __name__ == "__main__":
    main()