# 剧本评估离线评测报告


### 剧本评估方案指标对比评估报告

> [!NOTE]
> 当前系统采用 Mock LLM 进行评估，以下评测结果主要用于流程与结构验证，非模型实际推理能力上限限制。

| 评估指标 | 1. single_prompt_baseline | 2. fixed_workflow | 3. hybrid_workflow | 4. hybrid_workflow_with_tools |
| :--- | :---: | :---: | :---: | :---: |
| JSON 成功率 (json_success_rate) | 100.00% | 100.00% | 100.00% | 100.00% |
| 人物提取准确率 (character_extraction_accuracy) | 100.00% | 100.00% | 100.00% | 100.00% |
| 核心冲突准确率 (core_conflict_accuracy) | 91.01% | 91.01% | 91.01% | 91.01% |
| 证据引用准确率 (evidence_precision) | 10.00% | 65.00% | 85.00% | 85.00% |
| 无依据评价比例 (unsupported_claim_rate) | 90.00% | 30.00% | 10.00% | 10.00% |
| 质检缺陷检出率 (review_issue_detection_rate) | 0.00% | 0.00% | 16.67% | 16.67% |
| 工作流完成率 (workflow_success_rate) | 100.00% | 100.00% | 100.00% | 100.00% |
| 平均工具调用次数 (avg_tool_calls) | 0.00 | 0.00 | 0.00 | 8.30 |
| 平均执行延迟/毫秒 (avg_latency_ms) | 1.79 ms | 2.04 ms | 21.45 ms | 24.56 ms |
| 工具降级率 (fallback_rate) | 0.00% | 0.00% | 0.00% | 0.00% |
| 平均综合质量得分 (avg_quality_score) | 63.60 | 80.40 | 97.40 | 97.40 |
| 平均证据得分 (avg_evidence_score) | 37.00 | 89.00 | 98.00 | 98.00 |
| 平均建议可执行得分 (avg_actionable_score) | 68.50 | 68.50 | 100.00 | 100.00 |
| 平均一致性得分 (avg_consistency_score) | 94.00 | 94.00 | 100.00 | 100.00 |

说明：所有评估数据指标均由基准测试用例 (`benchmark.json`) 严格计算所得。