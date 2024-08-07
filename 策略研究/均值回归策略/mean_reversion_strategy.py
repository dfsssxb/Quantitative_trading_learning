import pandas as pd

# 股票策略模版
# 初始化函数,全局只运行一次
def init(context):
    # 设置基准收益：沪深300指数
    set_benchmark('000300.SH')
    # 打印日志
    log.info('策略开始运行,初始化函数全局只运行一次')
    # 设置股票每笔交易的手续费为万分之二(手续费在买卖成交后扣除,不包括税费,税费在卖出成交后扣除)
    set_commission(PerShare(type='stock',cost=0.0002))
    # 设置股票交易滑点0.5%,表示买入价为实际价格乘1.005,卖出价为实际价格乘0.995
    set_slippage(PriceSlippage(0.005))
    # 设置日级最大成交比例25%,分钟级最大成交比例50%
    # 日频运行时，下单数量超过当天真实成交量25%,则全部不成交
    # 分钟频运行时，下单数量超过当前分钟真实成交量50%,则全部不成交
    set_volume_limit(0.25,0.5)
    # 设置要操作的股票：如中石油
    g.security = '601857.SH'                    # 投资标的，中石油
    g.up = 0.05                                 # 价格向上波动的阈值
    g.down = 0.05                               # 价格向下波动的阈值
    g.T_up = 0.20                               # 止盈率
    g.T_down = 0.25                             # 止损率
    g.is_init = True                            # 初始建仓
    
    # 回测区间、初始资金、运行频率请在右上方设置

#每日开盘前9:00被调用一次,用于储存自定义参数、全局变量,执行盘前选股等
def before_trading(context):

    # 获取日期
    date = get_datetime().strftime('%Y-%m-%d %H:%M:%S')

    # 打印日期
    log.info('{} 盘前运行'.format(date))

## 开盘时运行函数
def handle_bar(context, bar_dict):

    # 获取时间
    time = get_datetime().strftime('%Y-%m-%d %H:%M:%S')

    # 打印时间
    log.info('{} 盘中运行'.format(time))

        
    # 获取股票过去5天的收盘价数据
    closeprice = history(g.security, ['close'], 5, '1d', False, 'pre', is_panel=1)
    # 当前价格，以前一天的收盘价为依据
    currentprice = list(closeprice['close'])[-1]
    # 计算5日均线
    MA5 = closeprice['close'].mean()
    
    if g.is_init:
        # 初始建仓
        order_target_percent(g.security, 1)
        g.cost = currentprice
        g.is_init = False
        
        
    # 获取当前账户当前持仓市值
    market_value = context.portfolio.stock_account.market_value
    # 获取账户持仓股票列表
    stocklist = list(context.portfolio.stock_account.positions)
    log.info("当前价格：%.3f，均值： %.3f  " % (currentprice, MA5))
    if len(stocklist) > 0:
        # 止盈或止损
        if currentprice >= g.cost*(1+g.T_up) or currentprice <= g.cost*(1-g.T_down):
            # 卖出所有股票,使这只股票的最终持有量为0
            order_target(g.security, 0)
            log.info("止盈或止损卖出,当前价格：%.3f，均值： %.3f  " % (currentprice, g.cost))

    # 如果价格偏离5日均线以下的阈值,则全仓买入股票
    if currentprice < MA5*(1-g.down):
        # 记录这次买入
        log.info("价格偏离5日均线以下的阈值, 买入 %s" % (g.security))
        # 按目标市值占比下单
        order_target_percent(g.security, 1)
        g.cost = currentprice
    # 如果价格偏离5日均线以上的阈值,则清仓股票
    elif currentprice > MA5*(1+g.up):
        log.info("当前价格：%.3f，均值： %.3f  " % (currentprice, MA5))
        # 记录这次卖出
        log.info("价格偏离5日均线以上的阈值, 卖出 %s" % (g.security))
        # 卖出所有股票,使这只股票的最终持有量为0
        order_target(g.security, 0)


## 收盘后运行函数,用于储存自定义参数、全局变量,执行盘后选股等
def after_trading(context):

    # 获取时间
    time = get_datetime().strftime('%Y-%m-%d %H:%M:%S')
    # 打印时间
    log.info('{} 盘后运行'.format(time))
    log.info('一天结束')