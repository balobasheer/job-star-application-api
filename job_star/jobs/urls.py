from django.urls import path, include

from .views import (CourseDetailAPIView,
                    CourseUpdateAPIView, CourseDeleteAPIView,
                    CoursesListAPIView,  CoursesCreationAPIView,
                    JobListCreateAPIView, JobDetailAPIView,
                    JobUpdateAPIView, JobDestroyAPIView,
                    CohortListAPIView, CohortUpdateAPIView,
                    CohortCreationAPIView, CohortDetailAPIView,
                    CohortDestroyAPIView, CohortCountDownAPIView,
                    CohortListOnlyAPIView,CourseListOnlyAPIView,
                    AdminCourseListAPIView, JobPostedToday,
                    JobPostedOneWeeksAgo, JobPostedTwoWeeksAgo,
                    AllJobsPosted, AllInactiveJobAPIView
                    )

from applications.views import ApplicationListAPIView

app_name = 'job'

urlpatterns = [
    # courses urls
    path('courses/', CoursesListAPIView.as_view()),
    path('courses/create', CoursesCreationAPIView.as_view(), name='course-create'),
    path('all-courses/', AdminCourseListAPIView.as_view()),
    path('courses/<int:pk>', CourseDetailAPIView.as_view(), name='course-detail'),
    path('courses/<uuid:uuid>/edit', CourseUpdateAPIView.as_view()),
    path('courses/<uuid:uuid>/delete', CourseDeleteAPIView.as_view()),

    # Cohort urls
    path('cohorts', CohortListAPIView.as_view(), name='cohorts'),
    path('cohort/create', CohortCreationAPIView.as_view(), name='cohort-create'),
    path('cohort/<int:pk>', CohortDetailAPIView.as_view(), name='cohort-detail'),
    path('cohort-options', CohortListOnlyAPIView.as_view(), name='options'),
    path('cohort/<int:cohort_id>/course-options', CourseListOnlyAPIView.as_view()),
    path('cohort/<int:pk>/edit', CohortUpdateAPIView.as_view(), name='cohort-update'),
    path('cohort/<int:pk>/delete', CohortDestroyAPIView.as_view(), name='cohort-delete'),
    path('latest-cohort', CohortCountDownAPIView.as_view(), name='count-down'),

    # Job urls
    path('', JobListCreateAPIView.as_view(), name='job-list-create'),
    path('<int:pk>/detail', JobDetailAPIView.as_view(), name='job-detail'),
    path('<int:pk>/update', JobUpdateAPIView.as_view(), name='job-update'),
    path('<int:pk>/delete', JobDestroyAPIView.as_view(), name='job-delete'),
    path('<int:job_id>/applications', ApplicationListAPIView.as_view(), name='applications'),
    path('today', JobPostedToday.as_view(), name='one-week-ago'),
    path('a-week-ago', JobPostedOneWeeksAgo.as_view(), name='two-week-ago'),
    path('two-weeks-ago', JobPostedTwoWeeksAgo.as_view(), name='three-weeks-ago'),
    path('all-time', AllJobsPosted.as_view(), name='one-month-ago'),
    path('inactive-jobs', AllInactiveJobAPIView.as_view(), name='inactive-job')
]
