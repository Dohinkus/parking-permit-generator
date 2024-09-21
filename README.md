# parking-permit-generator
Automatically creates a parking permit on rpm2park.com,
saves a screenshot of the permit to the PC,
sends the screenshot in a discord channel,
and auto-renews the permit when it's about to expire.

NOTE: you must run the automatic_parking_permit.py as
administrator, or the parking permit auto-renewal will fail.
The delete_scheduled_permit_renewal.py tool to remove the
task from Windows Task Scheduler must also be run as
administrator, or the deletion will fail.

The easiest way to run these as admin right now is to
run cmd.exe as admin, and then run the python scripts through
there. I'm actively working on a better solution to this.

The screenshot, discord, and auto-renewal settings are all
boolean flags in the config.yaml to decide which features
you want to use or avoid.

This project was inspired by a $200 towing fee after there was a
3 hour gap between two of my parking permits, and I was towed.
