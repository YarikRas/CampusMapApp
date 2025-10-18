using UnityEngine;

public class RoomHighlighter : MonoBehaviour
{
    private Renderer rend;
    private Color originalColor;

    void Start()
    {
        rend = GetComponent<Renderer>();
        originalColor = rend.material.color;
    }

    void OnMouseDown()
    {
        rend.material.color = Color.yellow;
    }

    void OnMouseUp()
    {
        rend.material.color = originalColor;
    }
}