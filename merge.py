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
# 2. 【核心修改】动态修改 "🧠 AI" 出站组
# =======================================================
target_tag = "🧠 AI"
new_outbound = "🐸 手动选择"
modified = False

if "outbounds" in base:
    for outbound in base["outbounds"]:
        # 找到 tag 为 "🧠 AI" 的 selector
        if outbound.get("tag") == target_tag:
            # 确保该项有 outbounds 列表
            if "outbounds" in outbound and isinstance(outbound["outbounds"], list):
                # 防止重复添加
                if new_outbound not in outbound["outbounds"]:
                    outbound["outbounds"].append(new_outbound)
                    modified = True
                    print(f"✅ 成功: 已将 '{new_outbound}' 添加到 '{target_tag}' 组")
                else:
                    print(f"ℹ️ 提示: '{target_tag}' 组中已包含 '{new_outbound}'，跳过添加")
            break

if not modified:
    print(f"⚠️ 警告: 未能在 base 配置中找到 '{target_tag}' 或修改失败")
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
