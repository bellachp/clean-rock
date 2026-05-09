locals {
  canonical_domain = "thatsacleanrock.earth"
  redirect_domain  = "thatsacleanrock.com"

  all_hostnames = [
    local.canonical_domain,
    "www.${local.canonical_domain}",
    local.redirect_domain,
    "www.${local.redirect_domain}",
  ]
}

resource "aws_route53_zone" "earth" {
  name    = local.canonical_domain
  comment = "${var.project} canonical apex"
}

resource "aws_route53_zone" "com" {
  name    = local.redirect_domain
  comment = "${var.project} redirect apex"
}

# CloudFront alias records — apex + www in each zone, both A and AAAA.
locals {
  hostname_zones = {
    "${local.canonical_domain}"     = aws_route53_zone.earth.zone_id
    "www.${local.canonical_domain}" = aws_route53_zone.earth.zone_id
    "${local.redirect_domain}"      = aws_route53_zone.com.zone_id
    "www.${local.redirect_domain}"  = aws_route53_zone.com.zone_id
  }
}

resource "aws_route53_record" "alias_a" {
  for_each = local.hostname_zones

  zone_id = each.value
  name    = each.key
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "alias_aaaa" {
  for_each = local.hostname_zones

  zone_id = each.value
  name    = each.key
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }
}

output "earth_nameservers" {
  description = "Paste these into Porkbun's nameserver settings for thatsacleanrock.earth"
  value       = aws_route53_zone.earth.name_servers
}

output "com_nameservers" {
  description = "Paste these into Porkbun's nameserver settings for thatsacleanrock.com"
  value       = aws_route53_zone.com.name_servers
}
