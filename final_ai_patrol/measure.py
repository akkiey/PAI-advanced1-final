import rclpy,json,time,sys
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from rclpy.signals import SignalHandlerOptions
rclpy.init(signal_handler_options=SignalHandlerOptions.NO); n=rclpy.create_node('evidence_recorder'); out=open(sys.argv[1],'w'); start=time.monotonic()
def odom(m):
 p=m.pose.pose.position; q=m.pose.pose.orientation
 out.write(json.dumps(dict(wall=time.monotonic()-start,sim=m.header.stamp.sec+m.header.stamp.nanosec/1e9,x=p.x,y=p.y,z=q.z,w=q.w,v=m.twist.twist.linear.x,omega=m.twist.twist.angular.z))+'\n'); out.flush()
def cmd(m):
 pass
s=n.create_subscription(Odometry,'/model/demoRobot/odometry',odom,10)
try:
 while time.monotonic()-start<float(sys.argv[2]):rclpy.spin_once(n,timeout_sec=.1)
except KeyboardInterrupt: pass
finally:out.close();n.destroy_node();rclpy.shutdown()
