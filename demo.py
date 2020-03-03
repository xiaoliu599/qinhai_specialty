#导入 tornado 中必要的类，导入 sqlalchemy 中必要的类,以及其它要用的类
from tornado.options import options,define
from tornado import httpserver
from tornado.web import RequestHandler,Application
from tornado.ioloop import IOLoop
from sqlalchemy import Column,String,Integer,Float,LargeBinary,DateTime,create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os,asyncio,datetime,base64,uuid

#python 3.8在Windows环境上写tornado得加上这句话，否则报错
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



#连接数据库 :mysql+(你下载的和MySQL连接的库)//<用户名：密码@主机名：端口号/数据库名？格式
engine=create_engine(
    'mysql+pymysql://root:root@localhost:3306/qinghai_specialty?charset=utf8'
)

#创建基础类，新建表时需要继承基类
Base=declarative_base()

#创建连接池
Session=sessionmaker(bind=engine)

#实例session对象,用于后面的数据操作
session=Session()


#用户信息表
class Userinfo(Base):
    #__tablename__ 用来设置表名
    __tablename__= 'user_info'

    # Column是列的意思，固定写法 Column(字段类型, 参数)
    # primary_key主键、index索引、nullable是否可以为空,autoincrement是否可以自增
    id=Column(Integer,primary_key=True,autoincrement=True,nullable=False)
    username=Column(String(20),nullable=False)
    password=Column(String(20),nullable=False)
    shopname=Column(String(30),nullable=False)
    phone=Column(String(11),nullable=False)
    address=Column(String(40),nullable=False)
    create_time=Column(DateTime,default=datetime.datetime.now)

    # 显示对象的时候打印名字
    def __str__(self):
        return self.name


#商品信息表
class Goodsinfo(Base):
    #设置表名
    __tablename__='goods_info'

    id=Column(Integer,primary_key=True,autoincrement=True,nullable=False)
    goods_name=Column(String(30),nullable=False)
    goods_image=Column(LargeBinary,nullable=False)
    goods_price=Column(Float(10),nullable=False)
    goods_oldprice=Column(Float(10),nullable=False)
    goods_unit=Column(String(10),nullable=False)
    goods_place=Column(String(20),nullable=False)
    create_time = Column(DateTime, default=datetime.datetime.now)

    # 显示对象的时候打印名字
    def __str__(self):
        return self.name


#测试商品插入数据库用（不测试时不要开启）
# img=open('static/image/沙果.png','rb')
# imgencode=base64.b64encode(img.read())
#
# shaguo=Goodsinfo(goods_name='沙果',goods_price=69,goods_oldprice=80,goods_unit='袋',goods_place='柴达木市',goods_image=imgencode)
#
# session.add(shaguo)
#
# session.commit()
# session.close()





#创建所有的表，有就忽视，没有就创建
Base.metadata.create_all(engine)


# getgoods()函数用来从数据库读取商品所有的信息，并将读取到的图片二进制解码并生成图片
# 返回的goodslist是存有商品信息的列表，可迭代；goodslist_len是商品信息列表的长度，不可迭代
def Getgoods():
    # goodlist列表用来存储商品信息，goodsimage列表用来存储商品图片二进制码
    goodslist=[]
    goodsimage=[]
    goods=session.query(Goodsinfo).all()
    for good in goods:
        goodslist.append(good)
        goodsimage.append(good.goods_image)
    goodslist_len=len(goodslist)
    #zip()里面可以包含两个可迭代的列表,下面这个循环将图片写入 static/image/中
    for i ,img in zip(range(1,goodslist_len+1),goodsimage):
        imagedecode=base64.b64decode(img)
        with open('static/image/{}.png'.format(i),'wb') as f:
            f.write(imagedecode)

    return goodslist,goodslist_len



#主页处理
class IndexHandler(RequestHandler):

    def get(self):
        #执行数据读取函数，将返回的值传递到主页上去
        goodslist,goodslist_len=Getgoods()

        self.render('main_page.html',username='',goodslist=goodslist,goodslist_len=goodslist_len)

#good.goods_name,good.goods_image,good.goods_price,good.goods_oldprice,good.goods_unit,good.goods_place



#获取当前用户类
# class BaseHandler(RequestHandler):
#
#     def get_current_user(self):
#         return self.get_secure_cookie('')


#错误处理类
# class WrongHandler(RequestHandler):
#
#     def get(self):
#         self.render('wrong_page.html')


#注册处理类
class RegisterHandler(RequestHandler):

    def get(self):
        self.render('register.html')

    def post(self):
        #获取页面传过来的注册的用户信息
        username=self.get_argument('username')
        password=self.get_argument('password')
        shopname=self.get_argument('shopname')
        address=self.get_argument('address')
        phone=self.get_argument('phone')

        #将它们添加到数据库，插入（Userinfo表）
        newuser=Userinfo(username=username,password=password,shopname=shopname,address=address,phone=phone)
        session.add(newuser)
        #添加后得用提交事务函数，否则无法添加
        session.commit()
        session.close()
        self.write('注册成功/n 请妥善保管您的账号密码哦~')
        #注册成功后跳转至登录页面
        self.redirect('login')





#登录处理类
class LoginHandler(RequestHandler):

    def get(self):
        self.render('login.html',wrong_info='')


    def post(self):
        #获取登录页面用户输入的账号密码
        username = self.get_argument('username')
        password = self.get_argument('password')

        #为当前登录的用户设置安全的cookie
        self.set_secure_cookie('name', username)

        #因为要登录成功后再次读取数据发送到主页上，所以再次执行读取数据函数
        goodslist, goodslist_len = Getgoods()

        #从数据库里查找有没有此用户
        result=session.query(Userinfo).all()

        # 从user_info表里获取用户信息，并进行匹配
        for r in result:
            if r.username==username and r.password==password:
                self.render('main_page.html',username=username,goodslist=goodslist,goodslist_len=goodslist_len)

        self.render('wrong_page.html')





#用户个人信息处理类
class PersonalHandler(RequestHandler):
    #查看
    def get(self):
        #获取当前登录的用户
        username=self.get_secure_cookie('name')
        #这里的获取的 username 是bytes格式，需用decode()转成string否则不好从数据库里匹配
        username_str=username.decode()
        userinfos=session.query(Userinfo).filter_by(username=username_str).all()

        self.render('personal_info.html',username=username,userinfos=userinfos)

    #修改
    def post(self):
        username=self.get_secure_cookie('username')
        cg_username=self.get_argument('username')
        cg_password=self.get_argument('password')
        cg_shopname=self.get_argument('shopname')
        cg_phone=self.get_argument('phone')
        cg_address=self.get_argument('address')

        change_dict={'username':cg_username,'password':cg_password,'shopname':cg_shopname,'phone':cg_phone,'address':cg_address}

        session.query(Userinfo).filter_by(username=username).update(change_dict)
        session.commit()
        self.render('change_ok.html')

#test




#主函数入口
if __name__ == '__main__':

    # 同来生成cookie_secret
    # base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)

    # login_url是应用登录表单的地址。
    # 如果get_current_user方法返回了一个假值，带有authenticated装饰器的处理程序将重定向浏览器的URL以便登录。
    settings = {
        # "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        "cookie_secret": "'gkbdtQcqRBmPVBZ7xgsbrWliJ5hPY03IkQzpHdNViHw='",
        # "xsrf_cookies": True,
        # "login_url": "/login"
    }

    app=Application([
        ('/',IndexHandler),
        ('/login',LoginHandler),
        ('/register',RegisterHandler),
        ('/personal_info',PersonalHandler),
        # ('/wrong_page',WrongHandler)

    ],static_path=os.path.join(os.path.dirname(__file__),'static'),**settings)

    #监听端口
    app.listen(8000)

    #运行项目
    IOLoop.current().start()

