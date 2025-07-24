# 项目说明

本项目是一个专注于银行业务费率问答的智能机器人，具备多重安全护栏设计，并对模型效果进行了系统性评估。其主要特点如下：

1. **业务聚焦与难点**：针对银行费率等高准确性需求的场景，机器人需确保回复的权威性和精确性。为此，系统采用了两种不同的LLM模型：优先调用结合结构化知识图谱（Knowledge Graph）的高精度LLM，若无法覆盖则退回到基于知识检索机制的LLM，提升整体答复的准确率和覆盖面。

2. **安全护栏设计**：为防止输出不当内容，系统在对话前后均集成了安全检测机制，包括毒性（toxicity）检测和拒答（refusal）检测，确保用户输入和机器人回复均符合合规与安全要求。

3. **多维度评估机制**：本项目通过涵盖4类不同意图（intention）的测试问题，对机器人进行评估，重点考察其在费率查询、对比、资格验证、流程咨询等主题下的表现。评估内容包括回复中的毒性、拒答情况，以及幻觉（hallucination）概率，全面衡量模型的优劣和实际应用价值。

整体结构如下：

## 1. 入口文件 main.py

`main.py` 是项目的入口文件。在 `main.py` 中，会调用 `agent_graph.py` 中的 `create_agent_graph()` 方法，构建整个问答流程的智能体图（Agent Graph），并通过该图对用户输入进行处理和响应。

## 2. 机器人问答流程

### 2.1 代码结构
在 `agent_graph.py` 中，定义了问答机器人的核心流程。整个流程分为以下几个步骤，每一步都是一个 Agent 节点：

- **(1) 对话前验证 & 安全过滤（prior_validation）**  
  检查用户输入是否包含有害、攻击性或不当内容（如毒性检测），如果检测不通过则拒绝服务。

- **(2) 语言检测（language）**  
  自动识别用户输入的语言（支持简体中文、繁体中文、英文等）。

- **(3) 意图识别（intention）**  
  判断用户问题属于哪种类型（如费率查询、对比、资格验证、流程咨询等）。

- **(4) 响应生成（generation）**  
  根据意图和语言，调用不同的 LLM 生成回复。

- **(5) 对话后验证 & 安全过滤（post_validation）**  
  对生成的回复再次进行安全性和合规性检测（如毒性检测、拒答检测），确保回复内容安全、合规。

### 2.2 安全护栏设计
本项目的安全护栏设计主要包括三类检测机制：

1. **毒性检测（toxicity）**  
   系统集成了 Hugging Face 的 toxigen_hatebert模型，用于识别用户输入和机器人回复中的有害、攻击性或不当内容。该模型对英文的敏感性较高，对中文的检测能力相对较弱，但整体能够有效拦截大部分不合规内容。毒性检测在对话前后均会执行，确保输入输出的安全性。

2. **拒答检测（refusal）**  
   拒答检测用于判断机器人回复是否为“拒绝回答”或“无法提供帮助”类的内容。项目采用 whylogs + langkit 的情感（sentiment）检测能力，对回复进行分析，及时发现和标记出拒答场景，便于后续统计和优化。

3. **数据泄露检测（data leakage）**  
   数据泄露检测旨在防止机器人输出敏感或隐私信息。目前尚无开箱即用的高质量模型，项目调研后发现 Hugging Face 上的 `span-marker-bert-tiny-fewnerd-coarse-super` 可用于实体识别，但其标签数量有限，难以满足银行业对数据安全的严格要求。后续如需上线此功能，建议针对银行业务场景进行专门的模型微调（fine-tuning），以提升检测的准确性和覆盖面。

通过上述多重安全护栏，项目能够在最大程度上保障问答过程的合规性和安全性，降低不当内容和敏感信息泄露的风险。

### 2.3 意图识别
意图识别（Intention Recognition）模块的核心目标是将用户问题归类到以下5种意图类型之一：

1. **费率查询（rate_query）**  
   直接询问某项银行服务的具体收费标准或费用明细。例如：“X服务的收费是多少？”、“What are the charges for bulk cheque deposits over 30 pieces per day?”

2. **对比（comparison）**  
   比较不同账户、服务或客户群体之间的费用、优惠或政策差异。例如：“Y和Z哪个更划算？”、“How do bulk cheque deposit fees differ for Senior Citizen Card holders vs. regular accounts?”

3. **资格验证（eligibility）**  
   验证用户是否符合某项费用减免、优惠或特权的条件。例如：“我是否符合免年费条件？”、“Are fee waivers available for Senior Citizen Card holders?”

4. **流程咨询（process）**  
   咨询办理某项业务、申请费用减免等的具体操作流程。例如：“如何申请免收纸质账单费？”、“How can a senior citizen apply for a paper statement fee waiver?”

5. **测试/其他（test/other）**  
   包含测试用例或无法归类到上述四类的其他问题。

**意图识别的实现与建议：**

- 当前项目采用 Qwen-plus 作为意图识别的 LLM。该模型参数量较大，未经过针对本业务场景的微调（fine-tuning），在意图分类上的准确性有限，尤其在细分场景下可能出现误判。
- 对于“费率查询”类问题，系统会优先调用结合结构化知识图谱（Knowledge Graph）的高精度LLM，以确保答复的权威性和准确性。
- 其余意图类型，则根据实际需求选择合适的 LLM 进行回复。

**后续优化建议：**

- 建议将意图识别模块替换为 BERT 或类似轻量级模型，并针对银行业务场景进行微调（fine-tuning），以显著提升意图分类的准确率和鲁棒性。
- 可结合现有的典型问题库（如 `data/questions.yaml`）进行有监督训练，提升模型对实际用户提问的适应能力。

**典型意图分类示例：**

| 用户问题示例                                                         | 识别意图         |
|---------------------------------------------------------------------|------------------|
| “What are the charges for bulk cheque deposits over 30 pieces?”     | 费率查询         |
| “Which is better, Senior Citizen Card or Integrated Account Card?”  | 对比             |
| “Do I qualify for fee waivers as a CSSA recipient?”                 | 资格验证         |
| “How can I apply for a paper statement fee waiver?”                 | 流程咨询         |
| “Which card is better for me?”                                      | 测试/其他        |


### 2.3 响应生成
1. **高精度费率查询**

1.1 采用Knowledge Graph（知识图谱）方式，将文档内容整理为由node（节点）和edge（边）组成的网络结构。节点类型包括：cards、service、fee_rule 和 footnote，每个节点都携带一段文字描述，并通过文档中的费率对应关系进行连接。（目前代码仅处理了第一页的费率查询内容）

1.2 查询时，会根据相关节点，自动检索并综合分析与之相连的多个节点，确保查询内容严格限定在所提供的文档范围内，同时全面覆盖所有相关信息，避免遗漏。

1.3 网络结构的扩展完全由用户控制，避免了算法黑盒带来的不可控风险，并可根据用户需求灵活连接不同业务内容。例如：
- 例1：如果想为 Prestige Banking Card 推荐基金理财服务，可以将 card node 与基金理财 service node 通过 Recommend 关系连接。
- 例2：每个人可单独作为一个 Person node，节点包含该人的所有描述信息。通过这些描述，可以连接到想推荐的业务节点，并控制不应推荐的业务（如对65岁以上老人，因合规要求不推荐高风险产品，则不建立相关连接）。

1.4 代码实现上，使用 `create_knowledge_graph.py` 进行建图，图数据存储在 Neo4j 云端服务器，通过 Neo4j API 及 Cypher 语法进行查询（目前为14天 trial 版）。这种网络结构的复杂度高于一般结构化数据，未来在大规模扩展时的性能表现尚待进一步调研。

2. **General 文档查询**

2.1 不进行结构化整理，直接提取文档原文，经过 split、tokenize 后存储在 ChromaDB 中。

2.2 查询时，采用 map-reduce 的 retrieval 方法，综合检索结果生成最终回答。

2.3 该方法虽然查询准确性不及结构化数据，但更适合处理 general 的对比类问题，并可在 Knowledge Graph 无法覆盖时作为兜底方案给出答案。

3. **两种方法的对比**

例子1：

例子2：
