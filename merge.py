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
# 2. 【出站组修改】动态调整 "🐸 手动选择" 到首位
# =======================================================
target_tag = "🧠 AI"
manual_node = "🐸 手动选择"
modified_count = 0

if "outbounds" in base:
    for outbound in base["outbounds"]:
        if "outbounds" in outbound and isinstance(outbound["outbounds"], list):
            ob_list = outbound["outbounds"]
            group_tag = outbound.get("tag", "未命名组")
            
            if group_tag == target_tag and manual_node not in ob_list:
                ob_list.insert(0, manual_node)
                modified_count += 1
            elif manual_node in ob_list:
                current_index = ob_list.index(manual_node)
                if current_index != 0:
                    ob_list.pop(current_index)
                    ob_list.insert(0, manual_node)
                    modified_count += 1

print(f"📊 出站组调整完毕: 共修改了 {modified_count} 个组")

# =======================================================
# 3. 合并 rule_set (定义部分)
# =======================================================
base_rule_sets = {r["tag"]: r for r in base.get("route", {}).get("rule_set", [])}
custom_rule_sets = custom.get("route", {}).get("rule_set", [])

for r in custom_rule_sets:
    base_rule_sets[r["tag"]] = r

base.setdefault("route", {})["rule_set"] = list(base_rule_sets.values())

# =======================================================
# 4. 【关键修正】智能插入 my_direct 规则
# =======================================================
base_rules = base.get("route", {}).get("rules", [])
custom_rules = custom.get("route", {}).get("rules", [])

priority_rule = None
other_custom_rules = []
target_rule_set_name = "my_direct"

# 4.1 提取高优先级规则
for rule in custom_rules:
    rs = rule.get("rule_set")
    is_priority = False
    
    if isinstance(rs, str) and rs == target_rule_set_name:
        is_priority = True
    elif isinstance(rs, list) and target_rule_set_name in rs:
        is_priority = True
        
    if is_priority:
        priority_rule = rule
    else:
        other_custom_rules.append(rule)

# 4.2 计算最佳插入位置 (这是之前失败的关键!)
# 我们必须把规则放在 'sniff' (嗅探) 和 'hijack-dns' 之后，否则 FakeIP 无法匹配域名
insert_index = 0
for i, rule in enumerate(base_rules):
    # 检查是否是功能性规则 (嗅探、DNS劫持、协议处理)
    # 如果包含 'action' (如 sniff, hijack-dns, resolve) 或者 'inbound' 限定
    # 这些规则必须保留在最前面
    if "action" in rule or "inbound" in rule:
        insert_index = i + 1
    else:
        # 一旦遇到第一个“逻辑路由规则” (如 clush_mode, geosite, ip_cidr 等)，就停止
        # 我们的规则要插在这个前面
        break

print(f"📍 计算最佳插入位置: Index {insert_index} (位于嗅探/DNS规则之后)")

# 4.3 构建最终规则列表
# 顺序: [Base的功能性规则] + [你的直连规则] + [Base的逻辑规则] + [其他自定义规则]

head_rules = base_rules[:insert_index]  # 嗅探、DNS等
tail_rules = base_rules[insert_index:]  #原本的 GeoSite 等

final_rules = []
final_rules.extend(head_rules) # 先放功能规则

if priority_rule:
    final_rules.append(priority_rule) # 🔥 插入直连规则
    print(f"🚀 [优先级] 已将 'my_direct' 插入到第 {insert_index + 1} 条 (嗅探之后，逻辑优先)")
else:
    print(f"⚠️ [警告] 未找到 '{target_rule_set_name}' 规则")

final_rules.extend(tail_rules) # 再放 Base 的逻辑规则
final_rules.extend(other_custom_rules) # 最后放其他

base["route"]["rules"] = final_rules

# =======================================================
# 5. 输出
output_filename = "merged_momo.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"🎉 修复完成! 配置文件已生成 -> {output_filename}")
