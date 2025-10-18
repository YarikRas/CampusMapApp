using UnityEngine;

public class ModelController : MonoBehaviour
{
    [Header("Настройки вращения")]
    public float rotationSpeed = 100f;
    public bool limitToYAxis = true;

    [Header("Настройки зума")]
    public float zoomSpeed = 2f;
    public float minZoom = 5f;
    public float maxZoom = 20f;

    private Camera cam;
    private Vector3 startRotation;

    void Start()
    {
        cam = Camera.main;
        startRotation = transform.eulerAngles;
    }

    void Update()
    {
        HandleRotation();
        HandleZoom();
    }

    void HandleRotation()
    {
        // Управление мышью (ПК)
        if (Input.GetMouseButton(0))
        {
            float rotX = Input.GetAxis("Mouse X") * rotationSpeed * Time.deltaTime;
            float rotY = Input.GetAxis("Mouse Y") * rotationSpeed * Time.deltaTime;

            if (limitToYAxis)
            {
                transform.Rotate(Vector3.up, -rotX, Space.World);
            }
            else
            {
                transform.Rotate(Vector3.up, -rotX, Space.World);
                transform.Rotate(Vector3.right, rotY, Space.World);
            }
        }

        // Управление пальцем (мобильный экран)
        if (Input.touchCount == 1)
        {
            Touch touch = Input.GetTouch(0);
            if (touch.phase == TouchPhase.Moved)
            {
                float rotX = touch.deltaPosition.x * rotationSpeed * Time.deltaTime;
                if (limitToYAxis)
                    transform.Rotate(Vector3.up, -rotX, Space.World);
                else
                    transform.Rotate(Vector3.up, -rotX, Space.World);
            }
        }
    }

    void HandleZoom()
{
    if (cam == null) return;

    // ---- ПК ----
    float scroll = Input.GetAxis("Mouse ScrollWheel");
    if (Mathf.Abs(scroll) > 0.01f)
    {
        if (cam.orthographic)
        {
            cam.orthographicSize -= scroll * zoomSpeed * 5f;
            cam.orthographicSize = Mathf.Clamp(cam.orthographicSize, minZoom, maxZoom);
        }
        else
        {
            cam.fieldOfView -= scroll * zoomSpeed * 100 * Time.deltaTime;
            cam.fieldOfView = Mathf.Clamp(cam.fieldOfView, minZoom, maxZoom);
        }
    }

    // ---- Телефон ----
    if (Input.touchCount == 2)
    {
        Touch touch0 = Input.GetTouch(0);
        Touch touch1 = Input.GetTouch(1);

        Vector2 prevTouch0 = touch0.position - touch0.deltaPosition;
        Vector2 prevTouch1 = touch1.position - touch1.deltaPosition;

        float prevMagnitude = (prevTouch0 - prevTouch1).magnitude;
        float currentMagnitude = (touch0.position - touch1.position).magnitude;

        float difference = currentMagnitude - prevMagnitude;

        if (cam.orthographic)
        {
            cam.orthographicSize -= difference * zoomSpeed * 0.02f;
            cam.orthographicSize = Mathf.Clamp(cam.orthographicSize, minZoom, maxZoom);
        }
        else
        {
            cam.fieldOfView -= difference * zoomSpeed * 0.02f;
            cam.fieldOfView = Mathf.Clamp(cam.fieldOfView, minZoom, maxZoom);
        }
    }
}

}
