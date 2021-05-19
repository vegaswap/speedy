from info import Info
import unittest
import token_addresses

class TestBasic(unittest.TestCase):

    def test_rmpl(self):
        i = Info()
        result = i.pool_info(token_addresses.RMPL)
        print (result)
        self.assertEqual(result['target_pair'], token_addresses.ETH_RMPL)
        self.assertEqual(result['token_addr0'], token_addresses.WETH)
        self.assertEqual(result['token_addr1'], token_addresses.RMPL)
        self.assertEqual(result['token_decimals'], 9)
        self.assertTrue(result['price_float']>0.0001)
        
    # def test_sushi(self):
    #     i = Info()
    #     result = i.pool_infoR(token_addresses.SUSHI)
    #     print (result)
    #     self.assertEqual(result['target_pair'], token_addresses.SUSHI_ETH)
    #     self.assertEqual(result['token_addr0'], token_addresses.SUSHI)
    #     self.assertEqual(result['token_addr1'], token_addresses.WETH)
    #     self.assertEqual(result['token_decimals'], 18)
    #     self.assertTrue(result['price_float']>0.0001)
        

if __name__ == '__main__':
    unittest.main()