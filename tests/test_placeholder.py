import unittest

class TestPlaceholder(unittest.TestCase):

    def test_placeholder_1(self):
        self.assertEqual(1, 1)

    def test_placeholder_2(self):
        self.assertTrue(True)

    def test_placeholder_3(self):
        self.assertIsNone(None)

if __name__ == '__main__':
    unittest.main()