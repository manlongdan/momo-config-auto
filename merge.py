import json
import urllib.request

# 两个远程文件 URL
URLS = [
    "https://raw.githubusercontent.com/qichiyuhub/rule/refs/heads/main/config/singbox/1.12.x/sub-momofake.json", # Base
    "https://raw.githubusercontent.com/manlongdan/rule_set/refs/heads/main/config/my_sub_momo.json"              # Custom
]

def fetch_json(url):
    print(f"⬇️ 正在下载: {url} ...")
    with urllib.request.urlopen(url) as response:
        return json.load(response)

# 1. 读取配置
try:
    base = fetch_json(URLS[0])
    custom = fetch_json(URLS[1])
except Exception as e:
    print(f"❌ 下载或解析 JSON 失败: {e}")
    exit(1)

# =======================================================
# 2. 【核心修改 A】动态调整 "🐸 手动选择" 到首位
# =======================================================
target_tag = "🧠 AI"
manual_node = "🐸 手动选择"
modified_count = 0  # ✅ 已恢复计数器

if "outbounds" in base:
    for outbound in base["outbounds"]:
        # 仅处理包含子出站列表的组 (Selector/URLTest)
        if "outbounds" in outbound and isinstance(outbound["outbounds"], list):
            ob_list = outbound["outbounds"]
            group_tag = outbound.get("tag", "未命名组")
            
            # 情况1：针对 "🧠 AI" 组，如果完全没有，则强制在首位插入
            if group_tag == target_tag and manual_node not in ob_list:
                ob_list.insert(0, manual_node)
                print(f"  ➕ [新增] '{group_tag}': 强制插入 '{manual_node}' 到首位")
                modified_count += 1
            
            # 情况2：针对所有组，如果已存在但不在第一位，则移动到首位
            elif manual_node in ob_list:
                current_index = ob_list.index(manual_node)
                if current_index != 0:
                    ob_list.pop(current_index) # 移除旧位置
                    ob_list.insert(0, manual_node) # 插入到头部
                    print(f"  🔄 [调整] '{group_tag}': '{manual_node}' 已移动到首位")
                    modified_count += 1

print(f"📊 出站组调整完毕: 共修改了 {modified_count} 个组")

# =======================================================
# 3. 合并 rule_set (定义部分)
# =======================================================
base_rule_sets = {r["tag"]: r for r in base.get("route", {}).get("rule_set", [])}
custom_rule_sets = custom.get("route", {}).get("rule_set", [])

for r in custom_rule_sets:
    base_rule_sets[r["tag"]] = r
    # print(f"  📦 加载/覆盖规则集: {r['tag']}")

base.setdefault("route", {})["rule_set"] = list(base_rule_sets.values())

# =======================================================
# 4. 【核心修改 B】合并 rules 并置顶 "my_direct" 规则
# =======================================================
base_rules = base.get("route", {}).get("rules", [])
custom_rules = custom.get("route", {}).get("rules", [])

priority_rule = None
other_custom_rules = []
target_rule_set_name = "my_direct"

# 筛选逻辑：找出 my_direct 规则
for rule in custom_rules:
    rs = rule.get("rule_set")
    is_priority = False
    
    # rule_set 可能是字符串也可能是列表，需兼容判断
    if isinstance(rs, str) and rs == target_rule_set_name:
        is_priority = True
    elif isinstance(rs, list) and target_rule_set_name in rs:
        is_priority = True
        
    if is_priority:
        priority_rule = rule
    else:
        other_custom_rules.append(rule)

# 构建最终规则列表： [最高优先级] + [Base规则] + [其他自定义规则]
final_rules = []

if priority_rule:
    final_rules.append(priority_rule) # 🚀 强制 Index 0
    print(f"🚀 [优先级] 已将 'my_direct' 规则锁定为全局第一条 (防止误走代理)")
else:
    print(f"⚠️ [警告] 自定义配置中未找到 '{target_rule_set_name}' 规则，无法提升优先级")

final_rules.extend(base_rules)
final_rules.extend(other_custom_rules)

base["route"]["rules"] = final_rules

# =======================================================
# 5. 输出最终文件
output_filename = "merged_momo.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"🎉 所有任务完成! 配置文件已生成 -> {output_filename}")
