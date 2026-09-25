from anonymize import anonymize

def test_mobile_number_removed():
    assert anonymize("Call 9812345678 now") == "Call [PHONE] now"

def test_country_code_number_removed():
    assert anonymize("Call +9779812345678") == "Call [PHONE]"

def test_landline_removed():
    assert anonymize("Call 01-4412345") == "Call [PHONE]"

def test_email_removed():
    assert anonymize("Mail ram.sharma@gmail.com today") == "Mail [EMAIL] today"

def test_account_number_removed():
    assert anonymize("A/c 123456789012 debited") == "A/c [NUMBER] debited"

def test_url_tracking_removed():
    text = "Visit http://esewa-verify.xyz/login?user=9812345678"
    assert anonymize(text) == "Visit http://esewa-verify.xyz/login?[REMOVED]"

def test_at_trick_preserved():
    text = "Open http://esewa.com.np@login-check.xyz"
    assert anonymize(text) == text

def test_amounts_kept():
    assert anonymize("Rs 50000 jitnubhayo") == "Rs 50000 jitnubhayo"