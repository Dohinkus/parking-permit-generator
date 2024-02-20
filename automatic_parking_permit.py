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

# set up logging
# Set up basic configuration for logging
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def wait_for_element(driver, config, element_id):
    """
    This function waits X seconds until an element appears on a website.
    X seconds is determined by the config file.
    :param driver: A browser driver.
    :param config: A dict filled by config.yaml.
    :param element_id: An ID of an HTML attribute on a website.
    :return:
    """
    return WebDriverWait(driver, config['timeout']).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )


def create_parking_permit(driver, config):
    """
    This function creates a parking permit on rpm2park.com for locations WITHOUT a visitor code
    by filling out the website's forms.
    :param driver: The browser driver.
    :param config: A dict filled by config.yaml.
    :return:
    """
    # opens the property (location) dropdown and selects 'config.property_location' option
    (Select(wait_for_element(driver, config, 'MainContent_ddl_Property'))
     .select_by_visible_text(config['property_location']))

    # remaining functions fill out text boxes, click next buttons, checks boxes, and clicks submit button

    # rpm2park.com page 1
    wait_for_element(driver, config, 'MainContent_txt_Apartment').send_keys(config['apartment_number_str'])
    wait_for_element(driver, config, 'MainContent_btn_PropertyNext').click()
    # rpm2park.com page 2
    wait_for_element(driver, config, 'MainContent_txt_Plate').send_keys(config['plate_number'])
    wait_for_element(driver, config, 'MainContent_txt_Make').send_keys(config['vehicle_make'])
    wait_for_element(driver, config, 'MainContent_txt_Model').send_keys(config['vehicle_model'])
    wait_for_element(driver, config, 'MainContent_txt_Color').send_keys(config['vehicle_color'])
    wait_for_element(driver, config, 'MainContent_btn_Vehicle_Next').click()
    wait_for_element(driver, config, 'MainContent_btn_Auth_Next').click()
    # rpm2park.com page 3
    wait_for_element(driver, config, 'MainContent_txt_Review_PlateNumber').send_keys(config['plate_number'])
    wait_for_element(driver, config, 'MainContent_cb_Confirm').click()
    wait_for_element(driver, config, 'MainContent_btn_Submit').click()


def save_screenshot_of_permit(driver, screenshot_file_path, config):
    """
    This function saves a screenshot of the parking permit.
    :param driver: A browser driver.
    :param screenshot_file_path: A screenshot filename (needs to include .png extension).
    :param config: A dict filled by config.yaml.
    :return:
    """
    # waits until the parking permit's QR Code is visible to take a screenshot of it
    WebDriverWait(driver, config['timeout']).until(
        EC.visibility_of_element_located((By.ID, 'MainContent_img_QRC'))
    )

    driver.save_full_page_screenshot(screenshot_file_path)


def schedule_program_to_renew_permit(driver):
    """
    This function uses Windows Task Scheduler to schedule the program to
    run again when a parking permit expires to automatically renew the permit.
    :param driver: A browser driver.
    :return:
    """
    pass


def delete_screenshot_of_permit(screenshot_file_path):
    if os.path.exists(screenshot_file_path):
        os.remove(screenshot_file_path)
    else:
        logging.error(f"Could not find and delete {screenshot_file_path}.")


async def send_screenshot_in_discord(driver, screenshot_file_path, config):
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
    This program loads the config.yaml file's data into a dict,
    creates a free visitor's parking permit on rpm2park.com,
    optionally saves a screenshot of the permit to the machine,
    optionally uploads the screenshot to a discord server,
    optionally uses Windows Task Scheduler to schedule the program to run again once the
    parking permit is about to expire to automatically renew the permit,
    and then finally closes itself.
    :return:
    """
    try:
        config = {}
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Config file '{config}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        sys.exit(1)

    if not config['i_read_the_config_warning']:
        print("Did not set up config correctly, read debug.log for details")
        logging.error(f"Read the config warning and then set the bool under it to true.")
        sys.exit(1)

    # Firefox has a full page screenshot function that Chrome lacks, so Firefox is used instead of Chrome
    with webdriver.Firefox() as driver:
        driver.get('https://rpm2park.com/visitors/')

        create_parking_permit(driver, config)

        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        screenshot_file_path = f"{config['screenshot_folder']}\\rpm2park_parking_permit_{current_time}.png"

        if config['save_screenshot_of_permit']:
            save_screenshot_of_permit(driver, screenshot_file_path, config)

        if config['send_screenshot_in_discord']:
            asyncio.run(send_screenshot_in_discord(driver, screenshot_file_path, config))

        if config['automatically_renew_permit']:
            schedule_program_to_renew_permit(driver)


if __name__ == '__main__':
    main()
