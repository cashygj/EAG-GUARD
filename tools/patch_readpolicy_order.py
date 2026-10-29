"""把"只读策略"提前到对象白名单之前。

踩坑：travel 的 get_restaurants_address(restaurant_names=[...]) 因为用户没点名餐厅，
被对象白名单判"不在 O"，模型拿不到地址 → 答复缺字段 → 任务失败。
只读策略本就要求"读取免审"，必须先于对象检查生效。
"""

from pathlib import Path

path = Path(r"D:\EAG-GUARD\src\eag_guard\pipeline.py")
text = path.read_text(encoding="utf-8")

# 1) 删掉原来位于对象检查之后的策略块
old_block = '''            # 只读策略（报告表 4-2，按域选择）：
            #   audit_all  —— 读取也完整审核；
            #   no_target  —— 只放行"无目标读取"（列频道、查余额），带对象的要审；
            #   allow_all  —— 读取一律免审。
            # 报告实测：slack 用 no_target（1.90% / 0.6667），banking 用 allow_all
            # （0% / 0.7778）；全放行套到 slack 会掉到 4.76% / 0.5143。
            if spec.read_only and not reasons:
                no_target = not action.args
                if self.config.read_policy == "allow_all" or (
                    self.config.read_policy == "no_target" and no_target
                ):
                    return Decision("fpr", True, (),
                                    detail={"action": action.signature(),
                                            "read_only": True,
                                            "read_policy": self.config.read_policy})
'''
if old_block in text:
    text = text.replace(old_block, "")
else:
    print("警告：原策略块未匹配")

# 2) 在工具检查之后、对象检查之前插入
anchor = "            obj = spec.object_of(action.args)"
new_block = '''            # 只读策略（报告表 4-2，按域选择）必须先于对象白名单：
            # audit_all 全审；no_target 只放行无目标读取；allow_all 读取免审。
            # 踩坑：对象检查跑在策略前面，travel 的
            # get_restaurants_address(restaurant_names=[...]) 被判"对象不在 O"，
            # 模型拿不到地址，答复缺字段，任务直接失败。
            if spec.read_only:
                no_target = not action.args
                if self.config.read_policy == "allow_all" or (
                    self.config.read_policy == "no_target" and no_target
                ):
                    return Decision("fpr", True, (),
                                    detail={"action": action.signature(),
                                            "read_only": True,
                                            "read_policy": self.config.read_policy})

'''
if anchor in text and "必须先于对象白名单" not in text:
    text = text.replace(anchor, new_block + anchor, 1)

path.write_text(text, encoding="utf-8")
print("已把只读策略提前:", "必须先于对象白名单" in text)
print("原策略块已移除:", old_block not in text)
