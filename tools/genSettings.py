#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json


def writeHelper(f, obj, pre, indent):
    ids = "    " * indent
    for t in obj:
        name = t["name"]
        key = name.replace(" ", "").replace("/", "").replace("+", "p")
        typename = t["type"]
        if typename == "Object":
            f.write(f"{ids}struct {key} {{\n")
            f.write(f"{ids}    QString pre;\n")
            f.write(f"{ids}    {key}(QString p) : pre(p) {{}}\n")
            writeHelper(f, t["sub"], "pre, ", indent + 1)
            f.write(f"{ids}}};\n")
            f.write(
                f"{ids}inline {key} get{key}(QString key) {{ return {key}(QStringList {{{pre} {json.dumps(name)}, key}}.join('/')); }}\n")
            f.write(f"{ids}inline void remove{key}(QString key) {{ SettingsManager::remove(SettingsManager::keyStartsWith(QStringList {{{pre} {json.dumps(name)}, key}}.join('/'))); }}\n")
            f.write(f"{ids}inline QStringList query{key}() {{ return SettingsManager::itemUnder(QStringList {{{pre} {json.dumps(name)}}}.join('/') + '/'); }}\n")
        elif typename == "QMap":
            final = t["final"]
            pname = t.get("plural", name)
            pkey = pname.replace(" ", "").replace("/", "").replace("+", "p")
            f.write(f"{ids}inline void set{key}(QString key, {final} data) {{ SettingsManager::set(QStringList {{{pre} {json.dumps(name)}, key}}.join('/'), data); }}\n")
            f.write(f"{ids}inline void remove{key}(QString key) {{ SettingsManager::remove({{QStringList {{{pre} {json.dumps(name)}, key}}.join('/')}}); }}\n")
            f.write(f"{ids}inline {final} get{key}(QString key) {{ return SettingsManager::get(QStringList {{{pre} {json.dumps(name)}, key}}.join('/')).value<{final}>(); }}\n")
            f.write(f"{ids}inline QStringList get{pkey}() {{ return SettingsManager::itemUnder(QStringList {{{pre} {json.dumps(name)}}}.join('/') + '/'); }}\n")
        else:
            f.write(
                f"{ids}inline void set{key}({typename} value) {{ SettingsManager::set({json.dumps(name)}, value); }}\n")
            if typename == "bool":
                f.write(
                    f"{ids}inline bool is{key}() {{ return SettingsManager::get({json.dumps(name)}).toBool(); }}\n")
            else:
                f.write(
                    f"{ids}inline {typename} get{key}() {{ return SettingsManager::get({json.dumps(name)}).value<{typename}>(); }}\n")


def writeInfo(f, obj, lst):
    for t in obj:
        name = t["name"]
        key = name.replace(" ", "").replace("/", "").replace("+", "p")
        typename = t["type"]
        desc = t.get("desc", name.replace('/', ' '))
        ui = t.get("ui", "")
        tip = t.get("tip", "")
        hlp = t.get("help", "")
        requireAllDepends = t.get("requireAllDepends", True)
        depends = t.get("depends", [])
        if typename == "Object":
            f.write(f"    QList<SettingInfo> LIST{key};\n")
            writeInfo(f, t["sub"], f"LIST{key}")
        f.write(f"    {lst}.append(SettingInfo {{{json.dumps(name)}, ")
        desccode = f"tr({json.dumps(desc)})"
        for lang in ["C++", "Java", "Python"]:
            if lang in desc:
                desccode = f"tr({json.dumps(desc.replace(lang, '%1'))}).arg(\"{lang}\")"
                break
        f.write(desccode)
        tempname = typename
        if typename == "QMap":
            final = t["final"]
            tempname = f"QMap:{final}"
        dependsString = "{"
        for depend in depends:
            dependsString += f"{{{json.dumps(depend.get('name', ''))}, [](const QVariant &var) {{ {depend.get('check', 'return var.toBool();')} }}}}, "
        dependsString += "}"
        f.write(f", \"{tempname}\", \"{ui}\", tr({json.dumps(tip)}), tr({json.dumps(hlp)}), {json.dumps(requireAllDepends)}, {dependsString}, ")
        if typename != "Object":
            if "default" in t:
                if typename == "QString":
                    f.write(json.dumps(t["default"]))
                else:
                    if isinstance(t["default"], bool):
                        f.write(str(t["default"]).lower())
                    else:
                        f.write(str(t["default"]))
            else:
                defs = {
                    'QString': '""',
                    'int': '0',
                    'bool': 'false',
                    'QRect': 'QRect()',
                    'QByteArray': 'QByteArray()',
                    'QVariantList': 'QVariantList()',
                    'QMap': 'QVariantMap()'
                }
                f.write(defs[typename])
        else:
            f.write(f'QVariant()')
        f.write(f', {t.get("param", "QVariant()")}')
        if typename == "Object":
            f.write(f", LIST{key}")
        f.write("});\n")


if __name__ == "__main__":
    obj = json.load(open(sys.argv[1], mode="r", encoding="utf-8"))
    head = """/*
 * Copyright (C) 2019-2020 Ashar Khan <ashar786khan@gmail.com>
 *
 * This file is part of CP Editor.
 *
 * CP Editor is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * I will not be responsible if CP Editor behaves in unexpected way and
 * causes your ratings to go down and or lose any important contest.
 *
 * Believe Software is "Software" and it isn't immune to bugs.
 *
 */

/*
 * This file is auto generated by tools/genSettings.py
 */

"""
    setting_helper = open("generated/SettingsHelper.hpp",
                          mode="w", encoding="utf-8")
    setting_helper.write(head)
    setting_helper.write("""#ifndef SETTINGSHELPER_HPP
#define SETTINGSHELPER_HPP

#include "Settings/SettingsManager.hpp"
#include <QFont>
#include <QRect>
#include <QVariant>

namespace SettingsHelper
{
""")
    writeHelper(setting_helper, obj, "", 1)
    setting_helper.write("""}

#endif // SETTINGSHELPER_HPP""")
    setting_helper.close()

    setting_info = open("generated/SettingsInfo.cpp",
                        mode="w", encoding="utf-8")
    setting_info.write(head)
    setting_info.write("""#include "Settings/SettingsInfo.hpp"
#include <QFontDatabase>
#include <QRect>
#include "Core/StyleManager.hpp"

QList<SettingsInfo::SettingInfo> SettingsInfo::settings;

void SettingsInfo::updateSettingInfo()
{
    settings.clear();
""")
    writeInfo(setting_info, obj, "settings")
    setting_info.write("};\n")
    setting_info.close()
