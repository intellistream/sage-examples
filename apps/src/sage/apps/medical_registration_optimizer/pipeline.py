from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    DoctorSlotFetcher,
    PatientDoctorMatcher,
    RegistrationPlanBuilder,
    RegistrationRequestSource,
    RegistrationSink,
)


def run_medical_registration_optimizer_pipeline(request_file: str, output_file: str) -> None:
    env = LocalEnvironment("medical_registration_optimizer")
    (
        env.from_batch(RegistrationRequestSource, input_file=request_file)
        .map(DoctorSlotFetcher)
        .map(PatientDoctorMatcher)
        .map(RegistrationPlanBuilder)
        .sink(RegistrationSink, output_file=output_file)
    )
    env.submit(autostop=True)
