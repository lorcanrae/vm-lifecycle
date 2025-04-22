import click
import subprocess


# TODO: all of this

# def describe_vm():
#     """Get the description of the VM"""
#     response = str(
#         subprocess.check_output(
#             [
#                 "gcloud",
#                 "compute",
#                 "instances",
#                 "describe",
#                 "--zone=",  # TODO
#                 "--project=",  # TODO
#             ]
#         )
#     )


# @click.command()
# def connect():
#     "Connect to VM in VS Code inside ~/code/<username>"
#     if not check_running(describe_vm()):
#         print("VM is stopped. Run `devm start` before trying to connect")
