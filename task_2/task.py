#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import argparse
import os
from datetime import datetime
import json
import jsonschema
from jsonschema import validate
from dotenv import load_dotenv


def main_loop():
    trains = []
    while True:
        command = get_command()
        if command == 'exit':
            break
        elif command == 'add':
            trains.append(add_train())
            if len(trains) > 1:
                trains.sort(key=lambda item: item.get('destination', ''))
        elif command == 'list':
            print_list(trains)
        elif command.startswith('select '):
            select_train(command, trains)
        elif command.startswith("save "):
            parts = command.split(maxsplit=1)
            file_name = parts[1]
            save_trains(file_name, trains)

        elif command.startswith("load"):
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                file_name = parts[1]
            else:
                os.environ.setdefault('TRAIN_DATA', 'data.json')
                file_name = os.environ.get("TRAIN_DATA")
            if not file_name:
                print("The data file name is absent", file=sys.stderr)
                sys.exit(1)
            trains = load_trains(file_name)
        elif command == 'help':
            print_help()
        else:
            print(f"Неизвестная команда {command}", file=sys.stderr)


def get_command():
    return input(">>> ").lower()


def add_train(destination=None, number=None, time=None):
    print(destination)
    print(number)
    print(time)
    if destination is None \
            and number is None \
            and time is None:
        destination = input("Название пункта назначения? ")
        number = input("Номер поезда? ")
        time = input("Время отправления ЧЧ:ММ? ")
    train = {
        'destination': destination,
        'number': int(number),
        'time': datetime.strptime(time, '%H:%M'),
    }
    return train


def print_list(trains):
    line = '+-{}-+-{}-+-{}-+-{}-+'.format(
        '-' * 4,
        '-' * 28,
        '-' * 14,
        '-' * 19
    )
    print(line)
    print(
        '| {:^4} | {:^28} | {:^14} | {:^19} |'.format(
            "No",
            "Название пункта назначения",
            "Номер поезда",
            "Время отправления"
        )
    )
    print(line)
    for idx, train in enumerate(trains, 1):
        print(
            '| {:>4} | {:<28} | {:<14} | {:>19} |'.format(
                idx,
                train.get('destination', ''),
                train.get('number', ''),
                train.get('time', 0).strftime("%H:%M")
            )
        )
    print(line)


def print_help():
    print("Список команд:\n")
    print("add - добавить отправление;")
    print("list - вывести список отправлений;")
    print("select <ЧЧ:ММ> - вывод на экран информации о "
          "поездах, отправляющихся после этого времени;")
    print("save <имя файла.json> - сохранить в файл")
    print("load <имя файла.json> - загрузить из файла")
    print("help - отобразить справку;")
    print("exit - завершить работу с программой.")


def select_train(command, trains):
    count = 0
    parts = command.split(' ', maxsplit=1)
    time = datetime.strptime(parts[1], '%H:%M')
    for train in trains:
        if train.get("time") > time:
            count += 1
            print(
                '{:>4}: {} {}'.format(
                    count,
                    train.get('destination', ''),
                    train.get("number")
                )
            )
    if count == 0:
        print("Отправлений позже этого времени нет.")


def save_trains(file_name, trains):
    if file_name.split('.', maxsplit=1)[-1] != "json":
        print("Несоответствующий формат файла", file=sys.stderr)
        return False
    try:
        list_of_files = os.listdir(os.path.split(os.getcwd())[0])
        index = list_of_files.index('.gitignore')
        flag = True
    except ValueError:
        flag = False
        print("Файл .gitignore не найден", file=sys.stderr)

    if flag:
        file = f"{os.path.split(os.getcwd())[0]}/.gitignore"
        with open(file, 'a', encoding="utf-8") as git_file:
            git_file.write(f"{file_name}\n")

    for i in trains:
        i['time'] = i['time'].time().strftime("%H:%M")
    with open(file_name, "w", encoding="utf-8") as fout:
        json.dump(trains, fout, ensure_ascii=False, indent=4)
    return True


def validate_json(json_data):
    with open("schema.json", "r", encoding="utf-8") as json_schema:
        schema = json.load(json_schema)
    try:
        validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as err:
        return False
    return True


def load_trains(file_name):
    if file_name.split('.', maxsplit=1)[-1] != "json":
        print("Несоответствующий формат файла", file=sys.stderr)
        return []

    if not os.path.exists(f"{os.getcwd()}/{file_name}"):
        print("Файл не существует", file=sys.stderr)
        return []

    with open(file_name, "r", encoding="utf-8") as fin:
        data = []
        try:
            data = json.load(fin)
            flag = validate_json(data)
        except Exception as e:
            print("Некоректный файл", file=sys.stderr)
            flag = False
        if flag:
            for i in data:
                i['time'] = datetime.strptime(i['time'], '%H:%M')
            return data
        else:
            return []


def main(command_line=None):
    file_parser = argparse.ArgumentParser(add_help=False)
    file_parser.add_argument(
        "--filename",
        action="store",
        help="Имя файла для хранения данных"
    )
    parser = argparse.ArgumentParser("trains")
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    subparsers = parser.add_subparsers(dest="command")
    add = subparsers.add_parser(
        "add",
        parents=[file_parser],
        help="Добавить новое отправление"
    )
    add.add_argument(
        "-trd",
        "--train_dest",
        action="store",
        required=True,
        help="Пункт назначения поезда"
    )
    add.add_argument(
        "-n",
        "--number",
        action="store",
        help="Номер поезда"
    )
    add.add_argument(
        "-t",
        "--time",
        action="store",
        required=True,
        help="Время отправления поезда"
    )
    _ = subparsers.add_parser(
        "display",
        parents=[file_parser],
        help="Вывод информации о всех поездах"
    )
    select = subparsers.add_parser(
        "select",
        parents=[file_parser],
        help="Выбрать поезда, отправляющиеся "
             "позже указанного времени"
    )
    select.add_argument(
        "-t",
        "--time",
        action="store",
        required=True,
        help="Время отправления"
    )
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    args = parser.parse_args(command_line)
    try:
        data_file = args.filename
        if not data_file:
            os.environ.setdefault('TRAIN_DATA', 'data.json')
            data_file = os.environ.get("TRAIN_DATA")
        if not data_file:
            print("The data file name is absent", file=sys.stderr)
            sys.exit(1)
        is_dirty = False
        if os.path.exists(data_file):
            trains = load_trains(data_file)
        else:
            trains = []
        if args.command == "add":
            trains.append(add_train(
                args.train_dest,
                args.number,
                args.time
            ))
            is_dirty = True
        elif args.command == "display":
            print_list(trains)
        elif args.command == "select":
            select_train(f"select {args.time}", trains)
        if is_dirty:
            save_trains(data_file, trains)
    except Exception as e:
        main_loop()


if __name__ == '__main__':
    main()
