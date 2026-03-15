"""
Risk Definitions Module

Defines catastrophic risks and helper functions for risk assessment.
Catastrophic risks are those that cannot be overridden, even by the master.
"""

from typing import List, Dict, Tuple


# Catastrophic risk categories that override all permissions
CATASTROPHIC_RISK_CATEGORIES = {
    'data_destruction': {
        'description': 'Complete loss of critical data without backup',
        'examples': ['DROP DATABASE', 'rm -rf /', 'format drive', 'delete all files'],
        'keywords': ['drop database', 'rm -rf', 'format', 'wipe', 'erase all', 'delete all'],
        'override_allowed': False
    },
    'physical_harm': {
        'description': 'Actions that could cause physical injury or safety risks',
        'examples': ['control hardware unsafely', 'disable safety systems', 'hardware damage'],
        'keywords': ['physical harm', 'injury', 'safety system', 'disable safety', 'hardware damage'],
        'override_allowed': False
    },
    'legal_violation': {
        'description': 'Criminal activity or severe legal violations',
        'examples': ['unauthorized access', 'data theft', 'fraud', 'unauthorized copying'],
        'keywords': ['illegal', 'criminal', 'theft', 'fraud', 'unauthorized access', 'hacking'],
        'override_allowed': False
    },
    'financial_catastrophe': {
        'description': 'Unrecoverable financial loss or bankruptcy',
        'examples': ['transfer all funds', 'delete financial records', 'liquidate all assets'],
        'keywords': ['transfer all funds', 'financial ruin', 'bankruptcy', 'liquidate all'],
        'override_allowed': False
    },
    'security_breach': {
        'description': 'Exposing credentials or critical security infrastructure',
        'examples': ['publish passwords', 'disable authentication', 'expose API keys'],
        'keywords': ['publish password', 'expose credentials', 'disable authentication', 'api key'],
        'override_allowed': False
    }
}

# Non-catastrophic risks that CAN be overridden
NON_CATASTROPHIC_RISKS = {
    'data_modification': {
        'description': 'Minor or recoverable data changes',
        'examples': ['update user record', 'modify configuration', 'change setting'],
        'override_allowed': True
    },
    'resource_consumption': {
        'description': 'Significant resource usage but not catastrophic',
        'examples': ['heavy computation', 'large file processing', 'memory intensive'],
        'override_allowed': True
    },
    'operational_risk': {
        'description': 'Service interruption or temporary unavailability',
        'examples': ['restart service', 'maintenance window', 'temporary downtime'],
        'override_allowed': True
    }
}


def is_catastrophic_risk(violations: List[Dict]) -> bool:
    """
    Check if any violation represents a catastrophic risk.
    
    Args:
        violations: List of violation dictionaries with 'severity' and other fields
        
    Returns:
        True if any violation is catastrophic, False otherwise
    """
    if not violations:
        return False
    
    for violation in violations:
        severity = violation.get('severity', '').lower()
        if severity == 'catastrophic':
            return True
    
    return False


def get_risk_category(violation: Dict) -> str:
    """
    Match a violation to a catastrophic risk category.

    Args:
        violation: Violation dictionary containing description and action

    Returns:
        Category name or 'unknown'
    """
    # Try both field names for backward compatibility (standardized vs old)
    description = violation.get('description', violation.get('violation_description', '')).lower()
    action = violation.get('action', '').lower()
    combined = f"{description} {action}".lower()

    for category_name, category_info in CATASTROPHIC_RISK_CATEGORIES.items():
        # Check keywords
        for keyword in category_info.get('keywords', []):
            if keyword.lower() in combined:
                return category_name

        # Check examples
        for example in category_info.get('examples', []):
            if example.lower() in combined:
                return category_name

    return 'unknown'
    return 'unknown'


def format_catastrophic_warning(violations: List[Dict]) -> str:
    """
    Format a detailed warning message for catastrophic risks.
    
    Args:
        violations: List of violation dictionaries
        
    Returns:
        Formatted warning string
    """
    if not violations:
        return ""
    
    warning_lines = [
        "\n🔒 CATASTROPHIC RISK DETECTED",
        "=" * 60,
        "This action poses an unacceptable level of risk and CANNOT be overridden.\n"
    ]
    
    for i, violation in enumerate(violations, 1):
        category = get_risk_category(violation)
        category_info = CATASTROPHIC_RISK_CATEGORIES.get(category, {})
        
        warning_lines.append(f"\n⚠️  VIOLATION {i}: {violation.get('mandate', 'Unknown')}")
        warning_lines.append(f"   Category: {category}")
        warning_lines.append(f"   Description: {violation.get('description', 'Unknown')}")
        warning_lines.append(f"   Reasoning: {violation.get('reasoning', 'Unknown')}")
        
        if category_info:
            warning_lines.append(f"   Risk Type: {category_info.get('description', '')}")
    
    warning_lines.extend([
        "\n" + "=" * 60,
        "For more information, see: docs/CATASTROPHIC_RISKS.md",
        "=" * 60 + "\n"
    ])
    
    return "\n".join(warning_lines)


def get_risk_assessment_summary(violations: List[Dict]) -> Dict[str, any]:
    """
    Generate a summary assessment of all violations.
    
    Args:
        violations: List of violation dictionaries
        
    Returns:
        Assessment dictionary with counts and categorization
    """
    assessment = {
        'total_violations': len(violations),
        'catastrophic_count': 0,
        'catastrophic_risks': [],
        'non_catastrophic_violations': [],
        'is_catastrophic': False,
        'risk_categories': {}
    }
    
    for violation in violations:
        severity = violation.get('severity', '').lower()
        
        if severity == 'catastrophic':
            assessment['catastrophic_count'] += 1
            assessment['catastrophic_risks'].append(violation)
            assessment['is_catastrophic'] = True
            
            category = get_risk_category(violation)
            if category not in assessment['risk_categories']:
                assessment['risk_categories'][category] = 0
            assessment['risk_categories'][category] += 1
        else:
            assessment['non_catastrophic_violations'].append(violation)
    
    return assessment
