# skills/Pruner_Skills.py
import ast
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


# 1. 定义强制输出的数据结构 (Schema)
class PrunerResult(BaseModel):
    relevant_lines: List[int] = Field(
        description="与用户问题最相关的代码行号列表，务必保持精准。例如: [10, 11, 12]"
    )

def apply_context_pruning(content: str, query: str):
    """
    [Agentic 重构版] 呼叫 Pruner Agent 处理上下文瘦身，并强制返回结构化数据
    """
    from Core.engine import get_agent
    pruner_agent = get_agent("Pruner")
    if not pruner_agent:
        return content[:1000] + "\n... (Error: Pruner agent not found) ..."

    lines = content.splitlines()
    indexed_content = "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
    task_input = f"【用户问题】：{query}\n\n【代码内容】：\n{indexed_content}"

    messages = [
        SystemMessage(content=pruner_agent.get_full_instructions()),
        HumanMessage(content=task_input)
    ]

    try:
        # 2. 调用第一步新增的结构化输出方法
        response_obj = pruner_agent.client.get_structured_completion(
            model=pruner_agent.model,
            messages=messages,
            response_schema=PrunerResult
        )

        # 如果报错了返回的是字符串
        if isinstance(response_obj, str):
            raise Exception(response_obj)

        # 3. 直接拿到类型安全的 List[int]
        target_line_nums = response_obj.relevant_lines

        if not target_line_nums:
            return content[:1000] + "\n... (裁剪失败，未提取到有效行号) ..."

        # 4. 扩充上下文逻辑：保留关键行及其前后各 2 行
        final_indices = set()
        for n in target_line_nums:
            # 过滤掉非法的行号（LLM 幻觉）
            if n < 1 or n > len(lines):
                continue
                
            for i in range(max(1, n-2), min(len(lines), n+2) + 1):
                final_indices.add(i-1)
        
        sorted_indices = sorted(list(final_indices))
        pruned_lines = []
        last_idx = -1
        for idx in sorted_indices:
            if idx >= len(lines):
                continue
                
            if last_idx != -1 and idx > last_idx + 1:
                pruned_lines.append(f"\n... [已省略 {idx - last_idx - 1} 行] ...\n")
            pruned_lines.append(f"{idx+1}: {lines[idx]}")
            last_idx = idx
            
        return "\n".join(pruned_lines)

    except Exception as e:
        return f"Error during pruning: {str(e)}\n\nOriginal Content (Partial):\n{content[:1000]}"


def generate_code_skeleton(code_content: str) -> str:
    """
    [内存优化核心]
    使用 AST 解析代码，保留类、函数签名和文档字符串，
    将函数体内容折叠为 '...'，从而极大压缩 Token 占用且保留语义。
    """
    try:
        tree = ast.parse(code_content)
    except SyntaxError:
        # 如果不是 Python 代码（如 JSON/HTML），回退到简单的首尾截断
        if len(code_content) > 500:
            return code_content[:200] + f"\n... [Omitted {len(code_content) - 400} chars] ...\n" + code_content[-200:]
        return code_content

    class SkeletonTransformer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # 保留函数签名和 Docstring
            new_body = []
            if ast.get_docstring(node):
                new_body.append(ast.Expr(value=ast.Constant(value=ast.get_docstring(node))))

            # 插入 ... 占位符
            new_body.append(ast.Expr(value=ast.Constant(value="...")))

            node.body = new_body
            return node

        def visit_ClassDef(self, node):
            # 继续递归处理类内部的方法
            self.generic_visit(node)
            return node

    # 执行转换
    transformer = SkeletonTransformer()
    new_tree = transformer.visit(tree)

    # 还原为代码字符串
    try:
        # ast.unparse 需要 Python 3.9+
        return ast.unparse(new_tree)
    except Exception:
        # 降级方案
        return code_content[:500] + "\n... (AST Unparse Failed) ..."