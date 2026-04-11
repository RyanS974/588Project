# Compliance Report: {{ project_name }}

**Generated on:** {{ date }}

## Compliance Summary

{{ compliance_summary }}

## Standards Compliance

{% for standard, result in standards_comparison.items() %}
### {{ standard }}

| Field | Value |
|-------|-------|
| Status | {% if result.compliant %}COMPLIANT{% else %}NON-COMPLIANT{% endif %} |
| Details | {{ result.details }} |
| Recommendations | {{ result.recommendations }} |

{% endfor %}

## Action Items

{% for item in action_items %}
- {{ item }}
{% endfor %}