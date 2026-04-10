package ru.it.solutions.suggest.complaint.app.model.mappers;

import ru.it.solutions.suggest.complaint.app.model.dto.AppealCreateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.AppealResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.AppealUpdateDto;
import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

@Mapper(componentModel = "spring")
public interface AppealMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "status", ignore = true)
    Appeal toEntity(AppealCreateDto createDto);

    AppealResponseDto toResponseDto(Appeal appeal);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntity(@MappingTarget Appeal target, AppealUpdateDto source);
}