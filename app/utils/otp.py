import random

def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    range_start = 10**(length-1)
    range_end = (10**length)-1
    return str(random.randint(range_start, range_end))
