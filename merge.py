import json
import urllib.request

# 两个远程文件 URL
URLS = [
    "https://raw.githubusercontent.com/qichiyuhub/rule/refs/heads/main/config/singbox/1.12.x/sub-momofake.json",
    "https://raw.githubusercontent.com/manlongdan/rule_set/refs/heads/main/config/my_sub_momo.json"
]

def fetch_json(url):
    print(f"正在下载: {url} ...")
    with urllib.request.urlopen(url) as response:
        return json.load(response)

# 1. 读取配置
try:
    base = fetch_json(URLS[0])   # 基础配置 (sub-momofake)
    custom = fetch_json(URLS[1]) # 自定义配置 (my_sub_momo)
except Exception as e:
    print(f"下载或解析 JSON 失败: {e}")
    exit(1)

# =======================================================
# 2. 【核心修改】动态调整 "🐸 手动选择" 到首位
# =======================================================
# 改动点：逻辑改为遍历所有组，包含即置顶；针对 AI 组若缺失则强制首位插入。
target_tag = "🧠 AI"
manual_node = "🐸 手动选择"
modified_count = 0

if "outbounds" in base:
    for outbound in base["outbounds"]:
        # 仅处理包含子出站列表的组 (Selector/URLTest)
        if "outbounds" in outbound and isinstance(outbound["outbounds"], list):
            ob_list = outbound["outbounds"]
            group_tag = outbound.get("tag", "未命名组")
            
            # 情况A：针对 "🧠 AI" 组，如果完全没有，则强制在首位插入
            if group_tag == target_tag and manual_node not in ob_list:
                ob_list.insert(0, manual_node)
                print(f"✅ [新增] 已将 '{manual_node}' 插入到 '{group_tag}' 的首位")
                modified_count += 1
                continue # 插入后即为第一，无需后续移动操作

            # 情况B：针对所有组（含AI），如果已存在但不在第一位，则移动到首位
            if manual_node in ob_list:
                current_index = ob_list.index(manual_node)
                if current_index != 0:
                    ob_list.pop(current_index) # 移除旧位置
                    ob_list.insert(0, manual_node) # 插入到头部
                    print(f"🔄 [调整] '{group_tag}' 组: '{manual_node}' 已移动到首位")
                    modified_count += 1

if modified_count == 0:
    print("ℹ️ 未进行任何修改（可能所有组已符合要求）")
# =======================================================


# 3. 合并 rule_set (保留 base 优先, custom 后覆盖/追加)
base_rule_sets = {r["tag"]: r for r in base.get("route", {}).get("rule_set", [])}
for r in custom.get("route", {}).get("rule_set", []):
    base_rule_sets[r["tag"]] = r
base.setdefault("route", {})["rule_set"] = list(base_rule_sets.values())

# 4. 合并 rules (追加 custom.rules 到末尾)
base_rules = base.get("route", {}).get("rules", [])
custom_rules = custom.get("route", {}).get("rules", [])

base_rules.extend(custom_rules)
base["route"]["rules"] = base_rules

# 5. 输出最终文件
output_filename = "merged_momo.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"🎉 合并并修改完成 -> {output_filename}")
