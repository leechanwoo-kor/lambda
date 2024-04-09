from nacl.signing import VerifyKey


DISCORD_PUBLIC_KEY = "059e2aa53828ecf2aebd55ce04f31837cd7e680a8d788540435c3b9f9cbef348"


def verify_request_signature(event):
    try:
        auth_sig = event["headers"].get("x-signature-ed25519")
        auth_ts = event["headers"].get("x-signature-timestamp")
        raw_body = event["body"]
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{auth_ts}{raw_body}".encode(), bytes.fromhex(auth_sig))
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False
    return True
