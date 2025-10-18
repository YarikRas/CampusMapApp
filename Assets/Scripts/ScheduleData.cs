using System;
using System.Collections.Generic;

[Serializable]
public class Lesson
{
    public string subject;
    public string room;
    public string teacher;
    public string time;
}

[Serializable]
public class DaySchedule
{
    public List<Lesson> lessons;
}

[Serializable]
public class Schedule
{
    public string group;
    public Dictionary<string, List<Lesson>> days;
}