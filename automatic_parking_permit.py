import argparse
import asyncio
import discord
import logging
import os
import sys
import yaml
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


def parse_arguments() -> argparse.Namespace:
    """
    This function parses the arguments entered at command line.
    :return: An argparse.Namespace where each attribute of this
    object corresponds to a command-line argument
    """
    parser = argparse.ArgumentParser()
    # allows user to specify a different config file
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to the config file (default: config.yaml)')
    # allows user to specify logging level as debug or not
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()


def setup_logging(verbose: bool):
    """
    This function sets up logging.
    :param verbose: A bool for enabling verbose logs.
    :return:
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=log_level)


def validate_config_file(config_file: str):
    """
    This function validates that config_file exists and is a file
    :param config_file: A config file name.
    :return:
    """
    if not os.path.exists(config_file):
        logging.error(f'Config file {config_file} does not exist.')
        sys.exit(1)
    if not os.path.isfile(config_file) or not config_file.endswith('.yaml'):
        logging.error(f'{config_file} is not a valid YAML file.')
        sys.exit(1)


def load_config(config_file: str) -> dict:
    """
    This function loads the contents of config_file into a dict.
    :param config_file: A config file name.
    :return: A dict filled by a config file.
    """
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        sys.exit(1)


def validate_config_warning(i_read_the_config_warning: bool):
    """
    This function validates that the user read the config warning.
    :param i_read_the_config_warning: A dict filled by a config file.
    :return:
    """
    if not i_read_the_config_warning:
        print("Did not set up config correctly, read debug.log for details")
        logging.error(f"Read the config warning and then set the bool under it to true.")
        sys.exit(1)


def wait_for_element(driver: webdriver, timeout_duration: int, element_id: str):
    """
    This function waits X seconds until an element appears on a website.
    X seconds is determined by the config file.
    :param driver: A browser driver.
    :param timeout_duration: The number of seconds until a TimeoutException is raised.
    :param element_id: An ID of an HTML attribute on a website.
    :return:
    """
    return WebDriverWait(driver, timeout_duration).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )


def create_parking_permit(driver: webdriver, config: dict):
    """
    This function creates a parking permit on rpm2park.com for locations WITHOUT a visitor code
    by filling out the website's forms.
    :param driver: The browser driver.
    :param config: A dict filled by a config file.
    :return:
    """
    # opens the property (location) dropdown and selects 'config.property_location' option
    (Select(wait_for_element(driver, config['timeout'], 'MainContent_ddl_Property'))
     .select_by_visible_text(config['property_location']))

    # remaining functions fill out text boxes, click next buttons, checks boxes, and clicks submit button

    # rpm2park.com page 1
    (wait_for_element(driver, config['timeout'], 'MainContent_txt_Apartment')
     .send_keys(config['apartment_number_str']))
    wait_for_element(driver, config['timeout'], 'MainContent_btn_PropertyNext').click()
    # rpm2park.com page 2
    wait_for_element(driver, config['timeout'], 'MainContent_txt_Plate').send_keys(config['plate_number'])
    wait_for_element(driver, config['timeout'], 'MainContent_txt_Make').send_keys(config['vehicle_make'])
    wait_for_element(driver, config['timeout'], 'MainContent_txt_Model').send_keys(config['vehicle_model'])
    wait_for_element(driver, config['timeout'], 'MainContent_txt_Color').send_keys(config['vehicle_color'])
    wait_for_element(driver, config['timeout'], 'MainContent_btn_Vehicle_Next').click()
    wait_for_element(driver, config['timeout'], 'MainContent_btn_Auth_Next').click()
    # rpm2park.com page 3
    (wait_for_element(driver, config['timeout'], 'MainContent_txt_Review_PlateNumber')
     .send_keys(config['plate_number']))
    wait_for_element(driver, config['timeout'], 'MainContent_cb_Confirm').click()
    wait_for_element(driver, config['timeout'], 'MainContent_btn_Submit').click()


def get_parking_permit_expiration_time(driver: webdriver):
    pass


def generate_screenshot_file_path(folder_path: str) -> str:
    """
    This function generates the unique name of a parking permit screenshot.
    :param folder_path: An absolute path to a folder for the screenshot.
    :return:
    """
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"{folder_path}\\rpm2park_parking_permit_{current_time}.png"


def save_screenshot_of_permit(driver: webdriver, screenshot_file_path: str, config: dict):
    """
    This function saves a screenshot of the parking permit.
    :param driver: A browser driver.
    :param screenshot_file_path: A screenshot filename (needs to include .png extension).
    :param config: A dict filled by a config file.
    :return:
    """
    # waits until the parking permit's QR Code is visible to take a screenshot of it
    wait_for_element(driver, config['timeout'], 'MainContent_img_QRC')

    driver.save_full_page_screenshot(screenshot_file_path)


def schedule_program_to_renew_permit(driver: webdriver):
    """
    This function uses Windows Task Scheduler to schedule the program to
    run again when a parking permit expires to automatically renew the permit.
    :param driver: A browser driver.
    :return:
    """
    pass


def delete_screenshot_of_permit(screenshot_file_path: str):
    """
    This function deletes a parking permit screenshot.
    :param screenshot_file_path: A file path of the screenshot.
    :return:
    """
    if os.path.exists(screenshot_file_path):
        os.remove(screenshot_file_path)
    else:
        logging.error(f"Could not find and delete {screenshot_file_path}.")


async def send_screenshot_in_discord(driver: webdriver, screenshot_file_path: str, config: dict):
    """
    This function uploads a screenshot from the machine to a discord server using a discord bot.
    :param driver: A browser driver.
    :param screenshot_file_path: A screenshot filename (needs to include file extension).
    :param config: A dict filled by config.yaml.
    :return:
    """
    # save a temporary screenshot if the user set the screenshotting flag to false
    # this screenshot will be deleted once the file is sent on discord
    if not config['save_screenshot_of_permit']:
        save_screenshot_of_permit(driver, screenshot_file_path, config)

    async with discord.Client(intents=discord.Intents.default()) as client:

        @client.event
        async def on_ready():
            """
            This function automatically runs when the discord bot connection is established
            and sends the screenshot.
            :return:
            """
            print(f'Logged in as {client.user}')
            channel = client.get_channel(config['discord_channel_id'])
            print(f'Sending PNG file named: {screenshot_file_path}')
            await channel.send(file=discord.File(screenshot_file_path))
            print(f'Logging off of {client.user}')
            await client.http.close()
            await client.close()

        await client.start(config['discord_bot_token'])

    # delete the temporary screenshot saved at the start of this function
    if not config['save_screenshot_of_permit']:
        delete_screenshot_of_permit(screenshot_file_path)


def main():
    """
    This program loads the --config argument's config file's data into a dict,
    creates a free visitor's parking permit on rpm2park.com,
    optionally saves a screenshot of the permit to the machine,
    optionally uploads the screenshot to a discord server,
    optionally uses Windows Task Scheduler to schedule the program to run again once the
    parking permit is about to expire to automatically renew the permit,
    and then finally closes itself.
    :return:
    """
    args = parse_arguments()
    setup_logging(args.verbose)

    logging.info(f'Using config file: {args.config}')
    validate_config_file(args.config)

    config = load_config(args.config)
    validate_config_warning(config['i_read_the_config_warning'])

    # Firefox has a full page screenshot function that Chrome lacks, so Firefox is used instead of Chrome
    with webdriver.Firefox() as driver:
        driver.get('https://rpm2park.com/visitors/')

        create_parking_permit(driver, config)

        # parking_permit_expiration_time = get_parking_permit_expiration_time(driver)

        screenshot_file_path = generate_screenshot_file_path(config['screenshot_folder'])

        if config['save_screenshot_of_permit']:
            save_screenshot_of_permit(driver, screenshot_file_path, config)

        if config['send_screenshot_in_discord']:
            asyncio.run(send_screenshot_in_discord(driver, screenshot_file_path, config))

        if config['automatically_renew_permit']:
            schedule_program_to_renew_permit(driver)


if __name__ == '__main__':
    main()
