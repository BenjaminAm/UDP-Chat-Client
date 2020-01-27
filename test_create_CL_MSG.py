from unittest import TestCase
import udp_messages as mess

class TestCreate_CL_MSG(TestCase):
    def test_create_CL_MSG(self):
        message = "Hello Yall"
        self.assertEqual(mess.create_CL_MSG(message), b"\x04" +b'\x00\x00\x00\n'+ b"Hello Yall")
        message *= 1000
        self.assertFalse(mess.create_CL_MSG(message))

