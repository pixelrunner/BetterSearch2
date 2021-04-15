#!/usr/bin/env python3

import asyncio
import json
from typing import Any
import settings

# import beeline
from aiohttp import ClientSession, ClientTimeout
from beeline.patch.urllib import *  # pylint: disable=wildcard-import
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail

# TODO Add Telegram module


def main(event: Any = None, context: Any = None) -> None:
    asyncio.run(main_async())

def build_params_list() -> list:
    params_list = []
    for centre_id in settings.leisure_centres:
        params = {
            "centre": centre_id,
            "courseGroupCategory": 1,  # Swimming
            "courseType": 1,  # Continous Programme
            "showFullCourses": True,  # Show classes that are full
            "dayOfWeek": settings.search_days,
            "level262": settings.course_level,  # 262 is the Swimbies category (was 'level196')
        }
        params_list.append(params)
    return params_list


async def main_async() -> None:
    beeline.init(dataset="swimscan")

    with beeline.tracer("main_async"):
        responses = await asyncio.gather(fetch_all())

        available_courses = find_available_courses(responses)

        if available_courses:
            # send_mail(available_courses)
            send_telegram(available_courses)

        async with ClientSession().get(settings.healthcheck_url) as response:
            await response.text()


@beeline.traced("fetch_all")  # type: ignore
async def fetch_all():
    params_list = build_params_list()
    async with ClientSession(timeout=ClientTimeout(total=10)) as session:  # ***
        results = await asyncio.gather(*[fetch(session, params) for params in params_list], return_exceptions=True)
        # await session.close()
    return results


@beeline.traced("fetch")  # type: ignore
async def fetch(session, params):
    async with session.get(
            settings.search_url,
            params={"filter": json.dumps(params)}
    ) as response:
        return await response.json()


@beeline.traced("find_available_courses")  # type: ignore
def find_available_courses(all_courses: tuple[Any, ...]) -> list[dict[str, Any]]:
    courses = []

    for centre in all_courses[0]:
        if isinstance(centre, TimeoutError):
            continue

        for course in centre.get("resultSet", {}).get("results", []):
            if str(course.get("courseId", "")) in settings.skipped_courses:
                continue

            if course.get("availability", {}).get("spaces", {}).get("free", 0) > 0:
                courses.append(course)

    return courses


''' # remove email section
@beeline.traced("send_mail")  # type: ignore
def send_mail(courses: list[dict[str, Any]]) -> None:
    message = "<strong>Courses available:</strong><br><br>"

    for course in courses:
        message += f"{course['centre']['name']}<br>"
        message += f"{course['schedule']['dayOfWeek']}s {course['schedule']['time']['start']} - {course['schedule']['time']['end']}<br>"
        message += f"{course['availability']['spaces']['free']} spaces available<br>"
        message += f"Course ID: {course['courseId']}<br><br>"

    mail = Mail(
        from_email=("swimscan@auto.tenzer.dk", "Swimscan"),
        to_emails="us@fihl-pearson.uk",
        subject="Swimming courses available",
        html_content=message,
    )
    sendgrid = SendGridAPIClient(os.environ.get("SENDGRID_TOKEN"))
    sendgrid.send(mail)
'''


@beeline.traced("send_telegram")  # type: ignore # TODO finish telegram function
def send_telegram(courses: list[dict[str, Any]]) -> None:
    message = "** Swimming Courses available!**\n\n"

    for course in courses:
        message += f"{course['centre']['name']}\n"
        message += f"{course['schedule']['dayOfWeek']}s {course['schedule']['time']['start']} - {course['schedule']['time']['end']}\n"
        message += f"{course['availability']['spaces']['free']} spaces available\n"
        message += f"Course ID: {course['courseId']}\n\n"

    # TODO send telegram bot message
    print(message) #T

if __name__ == "__main__":
    main()
