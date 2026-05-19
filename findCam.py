import cv2

# 把这里的 0 换成 1 试试，0 通常是笔记本原装拍脸的，1 是你插上的 USB 摄像头
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("❌ 摄像头被物理锁定或无权限！")
else:
    print("✅ 摄像头解锁成功！")
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Camera Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()