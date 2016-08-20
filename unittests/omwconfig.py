#!/usr/bin/env python2.7
import unittest
import os, sys
sys.path.append(os.path.abspath(".."))
from lib import omwconfig


class TestConfigEntry(unittest.TestCase):
    def test_init(self):
        data_line = "data=/path/to/mods"
        key, value = data_line.split("=")

        entry_parse = omwconfig.ConfigEntry(data_line)
        entry_explicit = omwconfig.ConfigEntry(key, value)

        self.assertEqual(entry_parse, entry_explicit)
        self.assertEqual(entry_parse.type(), "SETTING")
        self.assertEqual(entry_explicit.type(), "SETTING")

    def test_comment(self):
        comment_line = "# This is a comment!!!"
        entry = omwconfig.ConfigEntry(comment_line)

        self.assertEqual(entry, comment_line)
        self.assertEqual(entry.type(), "COMMENT")

    def test_invalid(self):
        invalid_line = "This line should raise an error!"
        self.assertRaises(ValueError, omwconfig.ConfigEntry, invalid_line)

    def test_blank(self):
        blank_line = "                  "
        self.assertRaises(ValueError, omwconfig.ConfigEntry, blank_line)

    def test_str(self):
        data_line = "data=/path/to/mods"
        entry = omwconfig.ConfigEntry(data_line)

        self.assertEqual(entry, data_line)

    def test_strip_whitespace(self):
        data_line = "    data = /path/to/someplace   "
        key, value = "data", "/path/to/someplace"
        entry = omwconfig.ConfigEntry(data_line)

        self.assertEqual(entry.key, key)
        self.assertEqual(entry.value, value)
        self.assertEqual(entry, "data=/path/to/someplace")


class TestConfigFile(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestConfigFile, self).__init__(*args, **kwargs)
        self.valid_cfg = "./openmw.cfg"
        self.invalid_cfg = "./openmw-invalid.cfg"

    def test_init(self):
        omwconfig.ConfigFile(self.valid_cfg)

    def test_invalid_init(self):
        self.assertRaises(ValueError, omwconfig.ConfigFile, self.invalid_cfg)

    # TODO: Fix these
    # def test_str(self):
    #     config = omwconfig.ConfigFile(self.valid_cfg)
    #     self.assertEqual(str(config), self.fixed_cfg_str)
    #
    # def test_eq(self):
    #     config = omwconfig.ConfigFile(self.valid_cfg)
    #
    #     self.assertEqual(config, self.fixed_cfg_str)
    #
    # def test_append(self):
    #     config = omwconfig.ConfigFile(self.valid_cfg)
    #     newentry = omwconfig.ConfigEntry("newkey", "newvalue")
    #     config.append(newentry)
    #
    #     new_config_str = self.fixed_cfg_str + "\n" + str(newentry)
    #     self.assertEqual(config, new_config_str)

    def test_insert(self):
        config = omwconfig.ConfigFile(self.valid_cfg)
        entry = omwconfig.ConfigEntry("NEW_KEY", "NEW_VALUE")
        config.insert(3, entry)

        self.assertTrue(entry in config)
        self.assertEquals(entry, config[3])

    def test_append(self):
        config = omwconfig.ConfigFile(self.valid_cfg)
        entry = omwconfig.ConfigEntry("NEW_KEY", "NEW_VALUE")
        config.append(entry)

        self.assertTrue(entry in config)
        self.assertEqual(entry, config[-1])

if __name__ == "__main__":
    unittest.main()
