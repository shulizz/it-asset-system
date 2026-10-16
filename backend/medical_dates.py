def validate_calibration_dates(calibration_date, calibration_expiry):
    if calibration_date and calibration_expiry and calibration_expiry < calibration_date:
        raise ValueError("校准到期时间不能早于校准时间")
