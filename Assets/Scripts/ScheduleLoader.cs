using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using TMPro;
using System.Collections.Generic;
using System;
using Newtonsoft.Json; // убедись, что у тебя установлен JSON.NET for Unity

public class ScheduleLoader : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI scheduleText;

    private string url = "https://raw.githubusercontent.com/YarikRas/CampusMapApp/refs/heads/main/schedule.json";

    void Start()
    {
        StartCoroutine(LoadSchedule());
    }

    IEnumerator LoadSchedule()
    {
        UnityWebRequest request = UnityWebRequest.Get(url);
        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            scheduleText.richText = true;

            try
            {
                Schedule schedule = JsonConvert.DeserializeObject<Schedule>(request.downloadHandler.text);
                scheduleText.text = FormatSchedule(schedule);
            }
            catch (Exception ex)
            {
                scheduleText.text = "Ошибка чтения JSON: " + ex.Message;
            }
        }
        else
        {
            scheduleText.text = "Ошибка загрузки: " + request.error;
        }
    }

    private string FormatSchedule(Schedule schedule)
    {
        string result = $"<b>Группа:</b> {schedule.group}\n\n";

        foreach (var day in schedule.days)
        {
            result += $"<b>{day.Key}</b>\n";
            foreach (var lesson in day.Value)
            {
                result += $"- {lesson.time}: {lesson.subject} ({lesson.room}) — {lesson.teacher}\n";
            }
            result += "\n";
        }

        return result;
    }
}
