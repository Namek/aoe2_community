record Api.CalendarEntry {
  id : Number,
  datetime : Time,
  description : String,
  sourceId : Number using "source_id",
  spectateOn : Maybe(Bool) using "spectate_on",
  spectateLink : Maybe(String) using "spectate_link"
}

record Event {
  id : Number,
  datetime : Time,
  name : String,
  sourceId : Number,
  spectate : SpectateMode
}

enum SpectateMode {
  OnChannel(String)
  Offline
  Unknown
}

record EventPatch {
  spectateOn : Maybe(Bool) using "spectate_on",
  spectateLink : Maybe(String) using "spectate_link"
}

store Calendar {
  state currentMonth = 0
  state currentYear = 0
  state currentDay = 0
  state today = Time.today()
  state daysData : Map(String, Array(Event)) = Map.empty()

  fun init {
    try {
      today =
        Time.today()

      next
        {
          currentMonth = Debug.log(Time.monthNum(today)),
          currentYear = Time.year(today),
          currentDay = Time.dayNum(today),
          today = today
        }

      refreshList()
    }
  }

  fun refreshList {
    sequence {
      App.setLoading(true)

      response =
        "#{@ENDPOINT}/api/calendar"
        |> Http.get()
        |> Http.send()

      entries =
        response.body
        |> Json.parse
        |> Maybe.toResult("Błąd pobierania kalendarza.")
        |> Result.flatMap(
          (json : Object) {
            decode json as Array(Api.CalendarEntry)
            |> Result.mapError((err : Object.Error) { "Błąd dekodowania kalendarza" })
          })

      next
        {
          daysData =
            entries
            |> Array.reduce(
              Map.empty(),
              (
                acc : Map(String, Array(Event)),
                entry : Api.CalendarEntry
              ) {
                try {
                  dateKey =
                    Number.toString(Time.day(entry.datetime)) + "-" + Number.toString(Time.month(entry.datetime)) + "-" + Number.toString(Time.year(entry.datetime))

                  events =
                    (Map.get(dateKey, acc) or [])
                    |> Array.push(
                      {
                        id = entry.id,
                        name = entry.description,
                        datetime = entry.datetime,
                        sourceId = entry.sourceId,
                        spectate =
                          case (entry.spectateOn) {
                            Maybe::Just(isOn) =>
                              if (isOn) {
                                case (entry.spectateLink) {
                                  Maybe::Just(link) => SpectateMode::OnChannel(link)
                                  => SpectateMode::Unknown
                                }
                              } else {
                                SpectateMode::Offline
                              }

                            Maybe::Nothing =>
                              SpectateMode::Unknown
                          }
                      })
                    |> Array.sortBy((event : Event) : Number { ` new Date(#{event}.datetime).getHours()` })

                  acc
                  |> Map.set(dateKey, events)
                }
              })
        }
    } catch Http.ErrorResponse => error {
      try {
        Debug.log(error)
        Promise.never()
      }
    } catch String => error {
      try {
        Debug.log(error)
        Promise.never()
      }
    } finally {
      App.setLoading(false)
    }
  }

  fun setPrevMonth {
    try {
      newMonth =
        Time.previousMonth(Time.from(currentYear, currentMonth, 1))

      next
        {
          currentYear = Time.year(newMonth),
          currentMonth = Time.monthNum(newMonth)
        }
    }
  }

  fun setNextMonth {
    try {
      newMonth =
        Time.nextMonth(Time.from(currentYear, currentMonth, 1))

      next
        {
          currentYear = Time.year(newMonth),
          currentMonth = Time.monthNum(newMonth)
        }
    }
  }

  fun daysInMonth (monthIndex : Number, year : Number) {
    `32 - new Date(#{year}, #{monthIndex}, 32).getDate()`
  }

  fun lastDaysFromPreviousMonth (curMonthNumber : Number, year : Number) : Array(Number) {
    try {
      curMonth =
        Time.from(year, curMonthNumber, 1)

      prevMonth =
        Time.previousMonth(curMonth)

      dayCount =
        daysInMonth(Time.monthNum(prevMonth) - 1, Time.year(prevMonth))

      firstDayThisMonth =
        `#{Time.startOf("month", curMonth)}.getDay()`

      if (firstDayThisMonth == 1) {
        []
      } else {
        Array.range(dayCount - firstDayThisMonth + 2, dayCount)
      }
    }
  }

  fun hashDate (day : Number, month : Number, year : Number) {
    "#{day}-#{month}-#{year}"
  }

  fun setSpectateMode (
    eventId : Number,
    spectateOn : Maybe(Bool),
    spectateLink : Maybe(String)
  ) {
    sequence {
      patch =
        {
          spectateOn = spectateOn,
          spectateLink = spectateLink
        }

      response =
        Http.empty()
        |> Http.url("#{@ENDPOINT}/api/calendar/#{eventId}")
        |> Http.method("PATCH")
        |> Http.withCredentials(true)
        |> Http.jsonBody(encode patch)
        |> Http.send()

      Calendar.refreshList()
    } catch Http.ErrorResponse => error {
      sequence {
        `alert("Sromotna klęska: " + JSON.stringify(#{error}))`
      }
    }
  }
}
