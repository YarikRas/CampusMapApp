using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using TMPro;
using Newtonsoft.Json;
namespace ScheduleData
{
    [Serializable]
public class Lesson
{
    public string pair;
    public string subject;
    public string teacher;
    public string room;
    public string note;
    public string week;
}

[Serializable]
public class Day
{
    public string day;
    public List<Lesson> lessons;
}

[Serializable]
public class Group
{
    public string group;
    public string type;
    public List<Day> days;
}

public class ScheduleManager : MonoBehaviour
{
    public string githubUrl = "https://raw.githubusercontent.com/YarikRas/CampusMapApp/refs/heads/main/schedule.json";
    public TMP_Dropdown groupDropdown;
    public TMP_Text scheduleText;
    public Button updateButton;

    private Dictionary<string, Group> allGroups;

    void Start()
    {
        if (updateButton != null)
            updateButton.onClick.AddListener(OnUpdateButtonClicked);

        StartCoroutine(LoadScheduleFromGitHub());
    }

    void OnUpdateButtonClicked()
    {
        StartCoroutine(LoadScheduleFromGitHub());
    }

    System.Collections.IEnumerator LoadScheduleFromGitHub()
    {
        using (UnityWebRequest request = UnityWebRequest.Get(githubUrl))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Ошибка загрузки JSON: " + request.error);
            }
            else
            {
                string jsonText = request.downloadHandler.text;
                allGroups = JsonConvert.DeserializeObject<Dictionary<string, Group>>(jsonText);

                SetupDropdown();
                scheduleText.text = "Выберите группу";
            }
        }
    }

    void SetupDropdown()
    {
        if (allGroups == null) return;

        groupDropdown.ClearOptions();

        List<string> options = new List<string> { "Выберите группу" };
        options.AddRange(allGroups.Keys);
        groupDropdown.AddOptions(options);

        groupDropdown.onValueChanged.RemoveAllListeners();
        groupDropdown.onValueChanged.AddListener(ShowTodaySchedule);
        groupDropdown.value = 0;
    }

    void ShowTodaySchedule(int groupIndex)
    {
        if (groupIndex == 0)
        {
            scheduleText.text = "Выберите группу";
            return;
        }

        string groupName = groupDropdown.options[groupIndex].text;
        Group group = allGroups[groupName];

        DateTime now = DateTime.Now;
        if (now.Hour >= 21)
            now = now.AddDays(1);

        string today = GetRussianWeekday(now.DayOfWeek);
        Day todayDay = group.days.Find(d => d.day == today);

        if (todayDay != null)
        {
            string displayText = $"<b><size=115%>{groupName}</size></b>\n<size=90%><i>{todayDay.day}</i></size>\n\n";

            foreach (var lesson in todayDay.lessons)
            {
                bool isCurrent = IsCurrentLesson(lesson);

                // выделение текущей пары цветом
                string startColor = isCurrent ? "<color=#FFD700>" : "";
                string endColor = isCurrent ? "</color>" : "";

                string[] parts = lesson.pair.Split('/');
                string pairName = parts[0].Trim();
                string time = (parts.Length > 1) ? parts[1].Trim() : "";

                displayText += $"{startColor}<size=90%><b>{pairName}</b> — <size=75%>{time}</size></size>\n";
                displayText += $"<size=100%>{lesson.subject}</size>\n";
                displayText += $"<size=75%><i>{lesson.teacher}</i></size>";

                if (!string.IsNullOrEmpty(lesson.note))
                    displayText += $"\n<size=75%><i>{lesson.note}</i></size>";

                displayText += $"{endColor}\n\n";
            }

            scheduleText.text = displayText;
        }
        else
        {
            scheduleText.text = $"{groupName} — {today}\nПар нет.";
        }
    }


        // Проверка текущей пары по времени
        bool IsCurrentLesson(Lesson lesson)
    {
        try
        {
            string[] parts = lesson.pair.Split('/');
            if (parts.Length < 2) return false;

            string[] times = parts[1].Trim().Split('-');
            if (times.Length < 2) return false;

            TimeSpan start = TimeSpan.Parse(times[0]);
            TimeSpan end = TimeSpan.Parse(times[1]);
            TimeSpan now = DateTime.Now.TimeOfDay;

            return now >= start && now <= end;
        }
        catch
        {
            return false;
        }
    }

    string GetRussianWeekday(DayOfWeek day)
    {
        switch (day)
        {
            case DayOfWeek.Monday: return "Понедельник";
            case DayOfWeek.Tuesday: return "Вторник";
            case DayOfWeek.Wednesday: return "Среда";
            case DayOfWeek.Thursday: return "Четверг";
            case DayOfWeek.Friday: return "Пятница";
            case DayOfWeek.Saturday: return "Суббота";
            case DayOfWeek.Sunday: return "Воскресенье";
            default: return "";
        }
    }
}
}