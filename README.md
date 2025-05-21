# EU (Emotional Understanding) Testing with GPT-4.1-nano

通过 python 代码，调用 gpt-4.1-nano 测试下 EU.jsonl

将结果记录到一个文件里面，记录下 gpt 返回的答案，以及正确答案

- 需要支持断开后，能继续上次的结果继续测试
- 需要支持传入测试几条记录
- 使用 conda 和 makefile

## 环境设置

1. 克隆本仓库
2. 创建并激活 conda 环境:

```
make env
conda activate agir-eu
```

3. 配置 API Key:

```
cp .env-example .env
```

然后编辑 `.env` 文件，添加你的 OpenAI API 密钥:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## 使用方法

### 运行完整测试

```
make run
```

### 限制测试记录数量

```
make run-limit limit=10
```

这将只测试前 10 条记录。

### 从上次中断处继续测试

```
make resume
```

## 结果查看

测试结果保存在 `results/results.jsonl` 文件中。每一行包含一个 JSON 对象，其中包含:

- 原始场景
- 正确的情绪和原因
- GPT 预测的情绪和原因
- 预测是否正确的指标

进度信息保存在 `results/progress.json` 文件中，用于支持断点续测。

测试完成后，程序会显示统计信息，包括:
- 情绪预测准确率
- 原因预测准确率
- 两者都正确的准确率