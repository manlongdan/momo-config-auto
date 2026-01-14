import json
import urllib.request
import ssl

# 忽略 SSL 验证
ssl._create_default_https_context = ssl._create_unverified_context

# 您的文件地址
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
base = fetch_json(URLS[0])
custom = fetch_json(URLS[1])

# =======================================================
# 2. 动态修改 "🧠 AI" 出站组 (原版逻辑)
# =======================================================
target_tag = "🧠 AI"
new_outbound = "🐸 手动选择"
modified = False

if "outbounds" in base:
    for outbound in base["outbounds"]:
        if outbound.get("tag") == target_tag:
            if "outbounds" not in outbound: outbound["outbounds"] = []
            
            # 优化：插入到第一个，而不是追加到最后
            if new_outbound not in outbound["outbounds"]:
                outbound["outbounds"].insert(0, new_outbound)
                modified = True
                print(f"✅ AI组: 已插入 '{new_outbound}'")
            break

# =======================================================
# 3. 合并 rule_set (原版逻辑)
# =======================================================
base_route = base.setdefault("route", {})
custom_route = custom.get("route", {})

base_rule_sets = {r["tag"]: r for r in base_route.get("rule_set", [])}
custom_rule_sets = {r["tag"]: r for r in custom_route.get("rule_set", [])}

base_rule_sets.update(custom_rule_sets)
base_route["rule_set"] = list(base_rule_sets.values())

# =======================================================
# 4. 【关键修正】合并路由规则 (Rules)
# =======================================================
base_rules = base_route.get("rules", [])
custom_rules = custom_route.get("rules", [])

# ❌ 原版错误写法: base_rules.extend(custom_rules)
# ✅ 修正写法: Custom 在前，Base 在后
final_rules = custom_rules + base_rules 
base_route["rules"] = final_rules
print(f"✅ 路由规则: 自定义规则({len(custom_rules)}) 已置顶 (修复Wise走代理)")

# =======================================================
# 5. 【新增功能】合并 DNS 配置 (DNS Rules)
# =======================================================
# 初始化 base 的 dns 结构
base_dns = base.setdefault("dns", {})
base_dns_rules = base_dns.get("rules", [])

# 获取 custom 的 dns 规则 (如果有)
if "dns" in custom and "rules" in custom["dns"]:
    custom_dns_rules = custom["dns"]["rules"]
    
    # 逻辑：自定义 DNS 规则同样要插到最前面，确保优先匹配
    # 例如：让直连域名强制走 223.5.5.5
    base_dns["rules"] = custom_dns_rules + base_dns_rules
    print(f"✅ DNS规则: 已合并 {len(custom_dns_rules)} 条自定义 DNS 规则")
else:
    print(f"ℹ️ 提示: my_sub_momo.json 中没有 'dns' 字段，本次未合并 DNS")

# =======================================================
# 6. 输出文件
# =======================================================
output_filename = "merged_momo.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"🎉 生成成功 -> {output_filename}")
