import json
import urllib.request
import ssl

# 忽略 SSL 证书验证
ssl._create_default_https_context = ssl._create_unverified_context

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
# 2. 动态修改 "🧠 AI" 出站组
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
                outbound["outbounds"].insert(0, new_outbound)
                modified = True
                print(f"✅ 成功: 已将 '{new_outbound}' 插入 '{target_tag}' 组首位")
            else:
                print(f"ℹ️ 提示: '{target_tag}' 组中已包含 '{new_outbound}'，跳过添加")
            break

# =======================================================
# 3. 合并 rule_set (资源集)
# =======================================================
base_route = base.setdefault("route", {})
custom_route = custom.get("route", {})

base_rule_sets = {r["tag"]: r for r in base_route.get("rule_set", [])}
custom_rule_sets = {r["tag"]: r for r in custom_route.get("rule_set", [])}

base_rule_sets.update(custom_rule_sets)
base_route["rule_set"] = list(base_rule_sets.values())

# =======================================================
# 4. 合并路由规则 (Route Rules)
# =======================================================
base_rules = base_route.get("rules", [])
custom_rules = custom_route.get("rules", [])

# 确保自定义路由规则优先级最高
final_rules = custom_rules + base_rules
base_route["rules"] = final_rules
print(f"✅ 路由规则合并完毕: 自定义规则({len(custom_rules)}) 优先")

# =======================================================
# 5. 【新增】合并 DNS 规则 (DNS Rules)
# =======================================================
# 只有当 custom 里写了 dns 规则时才执行
if "dns" in custom and "rules" in custom["dns"]:
    base_dns = base.setdefault("dns", {})
    base_dns_rules = base_dns.get("rules", [])
    custom_dns_rules = custom["dns"]["rules"]
    
    # 逻辑：自定义 DNS 规则插入到最前面，确保优先匹配
    base_dns["rules"] = custom_dns_rules + base_dns_rules
    print(f"✅ DNS 规则合并完毕: 您的直连 DNS 规则已生效")
else:
    print(f"ℹ️ 提示: 自定义配置中未发现 DNS 规则，跳过合并")

# =======================================================
# 6. 输出
# =======================================================
output_filename = "merged_momo.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"🎉 生成成功 -> {output_filename}")
