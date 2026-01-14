import json
import urllib.request
import ssl

# 忽略 SSL 证书验证 (防止 GitHub 拉取报错)
ssl._create_default_https_context = ssl._create_unverified_context

# 两个远程文件 URL
URLS = [
    "https://raw.githubusercontent.com/qichiyuhub/rule/refs/heads/main/config/singbox/1.12.x/sub-momofake.json",
    "https://raw.githubusercontent.com/manlongdan/rule_set/refs/heads/main/config/my_sub_momo.json"
]

def fetch_json(url):
    print(f"⬇️ 正在下载: {url} ...")
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.load(response)
    except Exception as e:
        print(f"❌ 下载或解析失败 [{url}]: {e}")
        exit(1)

# 1. 读取配置
base = fetch_json(URLS[0])   # 基础配置
custom = fetch_json(URLS[1]) # 自定义配置

# =======================================================
# 2. 动态修改 "🧠 AI" 出站组 (保留原逻辑)
# =======================================================
target_tag = "🧠 AI"
new_outbound = "🐸 手动选择"
modified = False

if "outbounds" in base:
    for outbound in base["outbounds"]:
        if outbound.get("tag") == target_tag:
            if "outbounds" not in outbound:
                outbound["outbounds"] = []
            
            if new_outbound not in outbound["outbounds"]:
                # 插入到第一位，方便选择
                outbound["outbounds"].insert(0, new_outbound)
                modified = True
                print(f"✅ 已将 '{new_outbound}' 插入 '{target_tag}' 组")
            break

if not modified:
    print(f"⚠️ 警告: 未找到 '{target_tag}' 组，跳过修改")

# =======================================================
# 3. 合并 rule_set (合并资源文件定义)
# =======================================================
base_route = base.setdefault("route", {})
custom_route = custom.get("route", {})

# 使用字典合并，确保 custom 中的同名 rule_set 会覆盖 base
base_rule_sets = {r["tag"]: r for r in base_route.get("rule_set", [])}
custom_rule_sets = {r["tag"]: r for r in custom_route.get("rule_set", [])}

base_rule_sets.update(custom_rule_sets)
base_route["rule_set"] = list(base_rule_sets.values())

# =======================================================
# 4. 【核心修改】合并 rules (优先级调整)
# =======================================================
base_rules = base_route.get("rules", [])
custom_rules = custom_route.get("rules", [])

# 🔥 修改点：将 custom_rules 放在最前面 (custom + base)
# 这样您的 wise.com 直连规则会排在第一位，绝对优先匹配
final_rules = custom_rules + base_rules

base_route["rules"] = final_rules
print(f"✅ 规则合并完毕: 自定义规则({len(custom_rules)}) 排在 基础规则({len(base_rules)}) 之前")

# 5. 输出最终文件
output_filename = "merged_momo.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"🎉 生成成功 -> {output_filename}")
