import sys
import math
import json
import logging
from random import choice, shuffle, sample, randint
from datetime import datetime, timedelta


logging.basicConfig(filename="log.txt",
                    encoding="utf-8",
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logger = logging.getLogger(__name__)


PATROL_START_AND_END = []
TIME_FORMAT = '%H:%M'


def read_info_from_file(filename):
    with open(filename, encoding="utf-8") as file:
        return file.read().splitlines()


def get_night_routine_time():
    """
    Returns routine time as whole hours in an integer format 
    for ease of use for comparisons in various functions.

    :return Routine hours in integer format.
    """

    tdelta = datetime.strptime(PATROL_START_AND_END[1], TIME_FORMAT) - \
             datetime.strptime(PATROL_START_AND_END[0], TIME_FORMAT)

    if tdelta.days < 0:
        tdelta = timedelta(
            days=0,
            seconds=tdelta.seconds,
            microseconds=tdelta.microseconds
        )

    # returns total patrol time in hours
    return int(tdelta.seconds/60/60)


def generate_platoon(information_list):
    """
    :param information_list: Contains the information read from the file provided as an argument 
                             or given by input via command line, not organized into squads.

    :return platoon: A list (platoon) of dictionaries (individual squad) 
                     that follows the structure shown in the example:
    [
        # Squad dictionary
        {
            "squad number": 1

            # Squad members - list (squad members) of dictionaries (individual soldier)
            "squad_members": [
                {
                    "id": 1
                    "rank": "PVT",
                    "name": "Diaz",
                    "driver": false,
                    "time_on_duty": [03:00]
                },
                {
                    "id": 2
                    "rank": "SGT",
                    "name": "Tigh",
                    "driver": false,
                    "time_on_duty": [21:00, 02:00]
                }
            ]
        },
        {
            "squad number": 2
            "squad_members": [
                {
                    "id": 3
                    "rank": "PVT",
                    "name": "King",
                    "driver": true,
                    "time_on_duty": [01:00]
                },
                {
                    "id": 4
                    "rank": "PVT",
                    "name": "Doe",
                    "driver": false,
                    "time_on_duty": []
                },
            ]
        }
    ]
    """
    information_list = information_list[1:]

    platoon = []
    squad = []
    squad_number = 1
    soldier_id = 0

    # Generate platoon information
    for soldier in information_list:
        if soldier == "":
            platoon.append({
                "squad_number": squad_number, 
                "squad_members": squad.copy()
            })
            squad_number += 1
            squad.clear()

        else:
            soldier = soldier.split(",")
            squad.append({
                "id": soldier_id,
                "rank": soldier[0],
                "name": soldier[1],
                "driver": soldier[2],
                "time_on_duty": []
            })
            logger.info("added soldier into {}. squad: {}".format(squad_number, str(soldier)))
            soldier_id += 1
    if squad is not None:
        platoon.append({
            "squad_number": squad_number, 
            "squad_members": squad.copy()
        })

    return platoon


def generate_night_routine_hours(platoon):
    """
    .param List of dictionaries, that contains information about a platoon.
    .return time_schedule: A list (platoon schedules) of dictionaries (squad schedules), 
                           contains each squad's patrol and stove watch schedules,
                           follows the structure shown in the example:
            [
                {
                    "stove_watch_schedule":[
                        {
                            "time": 00:00, 
                            "name": "Mick",
                            "id": "2"
                        },
                        {
                            "time": 01:00, 
                            "name": "Ley",
                            "id": "1"
                        },
                        {
                            "time": 02:00, 
                            "name": "Zac",
                            "id": "3"
                        }
                    ]
                    "patrol_schedule":[
                        {
                            "time": 01:00, 
                            "first_name": "Boomer",
                            "second_name": "Raynolds",
                            "first_id": "4",
                            "second_id": "5"
                        }
                    ]
                },
                {
                    "stove_watch_schedule":[
                        {
                            "time": 00:00, 
                            "name": "Yi",
                            "id": "6"
                        },
                        {
                            "time": 01:00, 
                            "name": "Leo",
                            "id": "7"
                        },
                        {
                            "time": 02:00, 
                            "name": "Buck",
                            "id": "8"
                        }
                    ]
                    "patrol_schedule":[
                        {
                            "time": 02:00, 
                            "first_name": "Ferretti",
                            "second_name": "Kawalsky",
                            "first_id": "4",
                            "second_id": "5"
                        }
                    ]
                }
            ]
    """

    platoon_size = 0
    for squad in platoon:
        platoon_size += len(squad["squad_members"])

    # calculate how many patrol hours for each squad
    squad_hours = []
    for squad in platoon:
        squad_hours.append(round(get_night_routine_time() *
                                 round(len(squad["squad_members"]) / platoon_size, 2), 2))

    # while sum of squads whole hours is smaller than total patrol time,
    # some squad's hours are rounded up by following the logic below.
    while sum([math.floor(element) for element in squad_hours]) < get_night_routine_time():

        # tuple structure = (squad_index_in_platoon, squad_hours_decimal)
        # squad_index_in_platoon - after the squad with the biggest decimal is found,
        # then its patrol hours are rounded up.

        # decimal - for comparing with other squads' hours, to determine which squad gets more hours.
        largest_decimal = (-1, 0)

        for i in range(len(squad_hours)):
            decimal = squad_hours[i] % 1

            if largest_decimal[1] < decimal:
                largest_decimal = (i, decimal)

            # if two squads have the same decimal size,
            elif largest_decimal[1] == decimal:
                # squad with more members gets more hours
                if len(platoon[largest_decimal[0]]) < len(platoon[i]):
                    largest_decimal = (i, decimal)
                elif len(platoon[largest_decimal[0]]) > len(platoon[i]):
                    largest_decimal = (i, decimal)
                # if both squads have the same amount of members, then one squad is randomly chosen for more hours.
                elif len(platoon[largest_decimal[0]]) == len(platoon[i]):
                    largest_decimal = (choice([i, largest_decimal[0]]), decimal)

        squad_hours[largest_decimal[0]] = math.ceil(squad_hours[largest_decimal[0]])

    squad_hours = [math.floor(element) for element in squad_hours]

    # generates a list, that contains the timeslots for stove watch members.
    time_schedule = []
    for i in range(len(platoon)):
        time_schedule.append({})

    current_time_patrol = PATROL_START_AND_END[0]
    time_obj_patrol = datetime.strptime(current_time_patrol, TIME_FORMAT)

    randomized_patrol_order = []
    for i in range(len(platoon)):
        randomized_patrol_order.append(i)

    shuffle(randomized_patrol_order)

    for squad_number in randomized_patrol_order:
        current_time = PATROL_START_AND_END[0]
        time_obj = datetime.strptime(current_time, TIME_FORMAT)
        stove_watch_schedule = []
        while True:
            stove_watch_schedule.append(
                {
                    "time": time_obj.strftime("%H:%M"), 
                    "name": "empty",
                    "id": "empty"
                })
            time_obj += timedelta(seconds=3600)
            if time_obj.strftime("%H:%M") == PATROL_START_AND_END[1]:
                break

        patrol_schedule = []
        hours = squad_hours[squad_number]
        while hours > 0:
            patrol_schedule.append(({
                "time": time_obj_patrol.strftime("%H:%M"), 
                "first_name": "empty",
                "second_name": "empty",
                "first_id": "empty",
                "second_id": "empty"
                }))
            time_obj_patrol += timedelta(seconds=3600)
            hours -= 1
        time_schedule[squad_number] = {
            "stove_watch_schedule": stove_watch_schedule, 
            "patrol_schedule": patrol_schedule.copy()
            }

    return time_schedule


def divide_night_routine_hours(platoon, time_schedule):
    """
    Fills platoon's time schedules with squad members.

    :param platoon: list of dictionaries which contains information about its squads.
    :param time_schedule: list of dictionaries which contains time schedule templates for each squad.
    :return time_schedule: list of dictionaries which contains organized time schedules.
    """

    # generates the schedules for each squad.
    for squad_number, squad in enumerate(platoon):
        squad_schedule = time_schedule[squad_number]

        # checks if there are drivers in the squad.
        drivers_in_squad = []
        for soldier in squad["squad_members"]:
            if soldier["driver"] == "yes":
                drivers_in_squad.append(soldier)

        # checks if the drivers can be used in the schedules while also getting six hours of consecutive sleep.
        if drivers_in_squad and get_night_routine_time() > 6:
            hours_per_driver = (get_night_routine_time() - 6) / len(drivers_in_squad)

            shuffle(drivers_in_squad)

            # if we can use the driver(s) in their squad's schedule,
            # we put them into the first or last hours of the stove watch schedule,
            # that way they get six hours of consecutive sleep.

            # whether the driver has the first stove-watch duty or the last one (if two drivers are in squad).
            first_watch = False

            for driver in drivers_in_squad:
                first_watch = not first_watch
                factor = 0 if first_watch else -1
                counter = math.ceil(hours_per_driver) if first_watch else math.floor(hours_per_driver)
                for i in range(counter):
                    logger.debug(squad_schedule["stove_watch_schedule"][1 * factor]["id"])
                    squad_schedule["stove_watch_schedule"][1 * factor]["id"] =  driver["id"]
                    squad_schedule["stove_watch_schedule"][1 * factor]["name"] = driver["name"]
                    driver["time_on_duty"].append(squad_schedule["stove_watch_schedule"][1 * factor]["time"])
                    factor = factor + 1 if first_watch else factor - 1

        # drivers are handled, now organizing patrols.
        # patrols must include two squad members at the same time.
        squad_for_calculating = squad["squad_members"].copy()
        for driver in drivers_in_squad:
            squad_for_calculating.remove(driver)

        # calculates the amount of available patrol pairs,
        # distributes the time slots evenly between the pairs.
        patrol_pairs_count = math.floor(len(squad_for_calculating) / 2)
        hours_per_pair = len(squad_schedule["patrol_schedule"]) / patrol_pairs_count
        pair_hours = []
        while len(pair_hours) < patrol_pairs_count:
            if len(pair_hours) + 1 == patrol_pairs_count:
                pair_hours.append(math.ceil(hours_per_pair))
            else:
                # one pair does atleast one hour of patrol.
                pair_hours.append(math.floor(hours_per_pair) if hours_per_pair > 1 else 1)
            # if there are more pairs than needed, then the pairs left over are dismissed.
            if sum(pair_hours) >= len(squad_schedule["patrol_schedule"]):
                break
        patrol_soldiers_list = sample(range(0, len(squad_for_calculating)), len(pair_hours) * 2)


        pair_counter = 0
        hour_index = 0
        # put the information of the pairs into the schedule information and vice versa.
        for i in range(0, len(patrol_soldiers_list), 2):
            hours = pair_hours[pair_counter]
            for _ in range(hours):
                patrol_hour = squad_schedule["patrol_schedule"][hour_index]
                patrol_hour["first_id"] = squad_for_calculating[patrol_soldiers_list[i]]["id"]
                patrol_hour["first_name"] = squad_for_calculating[patrol_soldiers_list[i]]["name"]
                squad_for_calculating[patrol_soldiers_list[i]]["time_on_duty"].append(patrol_hour["time"])
                patrol_hour["second_id"] = squad_for_calculating[patrol_soldiers_list[i + 1]]["id"]
                patrol_hour["second_name"] = squad_for_calculating[patrol_soldiers_list[i + 1]]["name"]
                squad_for_calculating[patrol_soldiers_list[i + 1]]["time_on_duty"].append(patrol_hour["time"])
                hour_index += 1
            pair_counter += 1

        # patrols are handled.
        # first - checks whether there is someone without any duties, those are added into the empty time slots first.
        for soldier in squad_for_calculating:
            if len(soldier["time_on_duty"]) == 0:
                for time_slot in squad_schedule["stove_watch_schedule"]:
                    if time_slot["id"] == "empty":
                        time_slot["id"] = soldier["id"]
                        time_slot["name"] = soldier["name"]
                        soldier["time_on_duty"].append(time_slot["time"])
                        break

        # if still empty time slots left, then soldiers are added based on their total sleep hours
        # (one with most hours gets duties).

        # if multiple soldiers have the same amount of sleep time,
        # then the selection is based on consecutive sleep, soldier with most cons. sleep gets duties.

        # if multiple soldiers have the same amount of sleep time and same amount of cons. sleep,
        # then one is chosen randomly between those soldiers to get the duties.
        while True:
            sleep_hours = 0
            cons_hours = []

            for index, soldier in enumerate(squad_for_calculating):
                if sleep_hours <= get_night_routine_time() - len(soldier["time_on_duty"]):
                    if sleep_hours < get_night_routine_time() - len(soldier["time_on_duty"]):
                        cons_hours = []
                    sleep_hours = get_night_routine_time() - len(soldier["time_on_duty"])

                    before_midnight = []
                    after_midnight = []
                    for time in soldier["time_on_duty"]:
                        if time[0] != "0":
                            before_midnight.append(time)
                        else:
                            after_midnight.append(time)
                    before_midnight.sort()
                    after_midnight.sort()
                    for after in after_midnight:
                        before_midnight.append(after)
                    time_point = PATROL_START_AND_END[0]

                    total_consecutive_sleep = 0
                    for time in before_midnight:
                        start_time = datetime.strptime(time_point, TIME_FORMAT)
                        tdelta = datetime.strptime(time, TIME_FORMAT) - start_time
                        start_time = datetime.strptime(time, TIME_FORMAT) + timedelta(hours=1)
                        if tdelta.days == -1:
                            tdelta += timedelta(days=1)
                        if total_consecutive_sleep < tdelta.seconds/60/60:
                            total_consecutive_sleep = tdelta.seconds/60/60

                    tdelta = datetime.strptime(PATROL_START_AND_END[1], TIME_FORMAT) - start_time
                    if tdelta.days == -1:
                        tdelta += timedelta(days=1)
                    if total_consecutive_sleep < tdelta.seconds/60/60:
                        total_consecutive_sleep = tdelta.seconds/60/60
                    cons_hours.append({
                            "index": index,
                            "id": soldier["id"],
                            "name": soldier["name"],
                            "total_consecutive_sleep": total_consecutive_sleep
                        })
            are_times_full = True
            for time_slot in squad_schedule["stove_watch_schedule"]:
                if time_slot["id"] == "empty":
                    are_times_full = False
                    break

            if are_times_full:
                break

            soldier = ""

            if len(cons_hours) == 1:
                soldier = squad_for_calculating[cons_hours[0]["index"]]
            else:
                largest_cons = 0
                with_largest_cons = []
                for soldier_cons in cons_hours:
                    if largest_cons < soldier_cons["total_consecutive_sleep"]:
                        with_largest_cons =[]
                        with_largest_cons.append(soldier_cons)

                if len(cons_hours) == 1:
                    soldier = squad_for_calculating[cons_hours[0]["index"]]
                else:
                    soldier = squad_for_calculating[cons_hours[randint(0, len(cons_hours) - 1)]["index"]]


            for time_slot in squad_schedule["stove_watch_schedule"]:
                if soldier and time_slot["time"] not in soldier["time_on_duty"] and time_slot["id"] == "empty":
                    time_slot["name"] = soldier["name"]
                    time_slot["id"] = soldier["id"]
                    soldier["time_on_duty"].append(time_slot["time"])
                    break
    return time_schedule


def read_info_from_cli():
    while True:
        try:
            time_start_string = input("When does nightly routine begin? (format: \"HH:MM\", don't forget zeros, exact hours only e.g. '06:00'): ")
            time_end_string = input("When does nightly routine end? (format: \"HH:MM\"), don't forget zeros, exact hours only e.g. '06:00'): ")
            PATROL_START_AND_END.append(time_start_string )
            PATROL_START_AND_END.append(time_end_string)
            get_night_routine_time()
            if time_start_string[2:] != ":00" or time_end_string[2:] != ":00":
                print("Full hours only.")
            else:
                break
        except ValueError:
            print("Given times couldn't be formatted into datetime objects. Are you sure you entered the times correctly?")
            logger.warning("Given times couldn't be formatted into datetime objects. Are you sure you entered the times correctly?")
            PATROL_START_AND_END.clear()
    platoon = []
    while True:
        try:
            platoon_size = int(input("How many squads are in the platoon? (1-4): "))
            if 1 <= int(platoon_size) <= 4:
                break
            else:
                print("Only one to four squads in a platoon.")
        except: 
            print("Number of squads has to be in an integer format.")

    id_counter = 0
    driver_counter = 0
    for i in range(platoon_size):
        squad = []
        if driver_counter < 2:
            print("PS make sure the platoon has at least two drivers, otherwise the platoon is invalid and schedules won't be generated. CURRENTLY {} DRIVERS.".format(driver_counter))
        while True:
            try:
                squad_size = int(input("How many soldiers are in {}. squad? (5-12): ".format(i+1)))
                if 5 <= squad_size <= 12:
                    break
                else:
                    print("Only five to 12 soldiers in a squad.")
            except:
                print("Squad size has to be in an integer format.")
        for soldier_index in range(squad_size):
            name = input("Enter {}. soldier's name: ".format(soldier_index+1))
            rank = input("Enter {}. soldier's rank (as an abbreviation, e.g. PVT = Private, SGT = Sergeant): ".format(soldier_index+1))

            while True:
                is_driver = input("Are they a driver? [Y/n]: ")

                if is_driver.lower() in ["y", "yes"]:
                    is_driver = True
                    driver_counter += 1
                    break
                elif is_driver.lower() in ["n", "no"]:
                    is_driver = False
                    break
                else:
                    print("Enter 'y' as in yes or 'n' as in no.")
                    
            soldier = {
                "id": id_counter,
                "rank": rank,
                "name": name,
                "driver": is_driver,
                "time_on_duty": []
            }

            squad.append(soldier)
            logger.info("added soldier into {}. squad: {}".format(i+1, str(soldier)))
            id_counter += 1

        platoon.append({
            "squad_number": i+1,
            "squad_members": squad
        })

    if driver_counter < 2:
        print("There has to be at least two drivers in the platoon, currently got only {} drivers.".format(driver_counter))
        print("Exiting program.")
        logger.critical("There has to be at least two drivers in the platoon, currently got only {} drivers. Exiting program.".format(driver_counter))
        return
    return platoon


def main():
    global PATROL_START_AND_END

    if len(sys.argv) < 2:
        platoon = read_info_from_cli()
        if not platoon:
            exit()
    else:
        information = read_info_from_file(sys.argv[1])
        PATROL_START_AND_END = information[0].strip().split(",")
        platoon = generate_platoon(information)

    time_schedule = generate_night_routine_hours(platoon)
    divide_night_routine_hours(platoon, time_schedule)

    into_file = input("Do you want to save the schedule into a file? [Y/n] ")
    if into_file.lower() == "y":
        with open('time_schedule.txt', 'w', encoding="utf-8") as file:
            json.dump(time_schedule, file, indent=4)

    into_file = input("Do you want to save the platoon info into a file? [Y/n] ")
    if into_file.lower() == "y":
        with open('platoon.txt', 'w', encoding="utf-8") as file:
            json.dump(platoon, file, indent=4)


if __name__ == "__main__":
    main()
