using System;
using System.Collections.Generic;
using UnityEngine;

public static class JsonHelper
{
    [Serializable]
    private class Wrapper<T>
    {
        public T[] Items;
    }

    public static T[] FromJson<T>(string json)
    {
        string wrapped = "{\"Items\":" + json + "}";
        return JsonUtility.FromJson<Wrapper<T>>(wrapped).Items;
    }

    public static string ToJson<T>(T[] array, bool prettyPrint = false)
    {
        var wrapper = new Wrapper<T> { Items = array };
        return JsonUtility.ToJson(wrapper, prettyPrint);
    }

    // ✅ исправленный метод без MiniJson
    public static Dictionary<string, T> FromJsonDictionary<T>(string json)
    {
        var result = new Dictionary<string, T>();

        // Убираем пробелы и внешние фигурные скобки
        json = json.Trim().TrimStart('{').TrimEnd('}');

        // Разбиваем по группам
        string[] entries = json.Split(new[] { "}," }, StringSplitOptions.RemoveEmptyEntries);
        foreach (var entry in entries)
        {
            int colonIndex = entry.IndexOf(':');
            if (colonIndex < 0) continue;

            string key = entry.Substring(0, colonIndex).Trim().Trim('"');
            string valueJson = entry.Substring(colonIndex + 1).Trim();

            if (!valueJson.EndsWith("}")) valueJson += "}";

            try
            {
                T value = JsonUtility.FromJson<T>(valueJson);
                result[key] = value;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"⚠️ Ошибка парсинга группы '{key}': {e.Message}");
            }
        }

        return result;
    }
}
