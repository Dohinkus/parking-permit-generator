import subprocess


def delete_task(task_name: str):
    """
    This function deletes a task in Windows Task Scheduler.
    :param task_name: A task's name.
    :return:
    """
    try:
        subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'], check=True)
        print(f"Task '{task_name}' deleted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to delete task '{task_name}'. Error: {e}")


def main():
    """
    This program deletes all tasks made by automatic_parking_permit.py.
    :return:
    """
    # must have admin permissions to succeed
    delete_task('AutomaticParkingPermitRenewal')


if __name__ == '__main__':
    main()
